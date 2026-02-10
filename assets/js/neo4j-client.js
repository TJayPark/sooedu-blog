// Neo4j Proxy Client for Soo Edu Curriculum Viewer
// Connects to local Neo4j proxy server (http://127.0.0.1:3939)

const NEO4J_PROXY_URL = 'http://127.0.0.1:3939/query';

class Neo4jClient {
    constructor() {
        this.cache = new Map();
    }

    /**
     * Execute a Cypher query through the proxy
     * @param {string} query - Cypher query
     * @param {Object} params - Query parameters
     * @param {number} maxRecords - Maximum records to return
     * @returns {Promise<Array>} Query results
     */
    async query(query, params = {}, maxRecords = 200) {
        const cacheKey = JSON.stringify({ query, params });

        // Check cache first
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(NEO4J_PROXY_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query,
                    params,
                    max_records: maxRecords
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const records = data.records || [];

            // Cache successful results
            this.cache.set(cacheKey, records);

            return records;
        } catch (error) {
            console.error('Neo4j query error:', error);
            throw new Error(`데이터를 불러올 수 없습니다: ${error.message}`);
        }
    }

    /**
     * Get curriculum by level
     * @param {string} level - Student level (Beginner, Intermediate, Advanced)
     * @returns {Promise<Array>} Curriculum items
     */
    async getCurriculumByLevel(level) {
        const query = `
            MATCH (c:Curriculum)
            WHERE c.level = $level
            RETURN c.title as title, 
                   c.description as description,
                   c.level as level,
                   c.topics as topics,
                   c.duration_weeks as duration
            ORDER BY c.order
        `;

        return await this.query(query, { level });
    }

    /**
     * Get curriculum by interest
     * @param {string} interest - Interest category
     * @returns {Promise<Array>} Curriculum items
     */
    async getCurriculumByInterest(interest) {
        const query = `
            MATCH (c:Curriculum)-[:MATCHES_INTEREST]->(i:Interest)
            WHERE i.name = $interest
            RETURN c.title as title,
                   c.description as description,
                   c.level as level,
                   c.topics as topics,
                   c.duration_weeks as duration
            ORDER BY c.level, c.order
        `;

        return await this.query(query, { interest });
    }

    /**
     * Get all available levels
     * @returns {Promise<Array>} List of levels
     */
    async getLevels() {
        const query = `
            MATCH (c:Curriculum)
            RETURN DISTINCT c.level as level
            ORDER BY c.level
        `;

        const results = await this.query(query);
        return results.map(r => r.level);
    }

    /**
     * Get all available interests
     * @returns {Promise<Array>} List of interests
     */
    async getInterests() {
        const query = `
            MATCH (i:Interest)
            RETURN i.name as name, i.description as description
            ORDER BY i.name
        `;

        return await this.query(query);
    }

    /**
     * Get personalized curriculum for a student
     * @param {string} studentId - Student ID
     * @returns {Promise<Object>} Student info and recommended curriculum
     */
    async getPersonalizedCurriculum(studentId) {
        const query = `
            MATCH (s:Student {id: $studentId})
            OPTIONAL MATCH (s)-[:HAS_INTEREST]->(i:Interest)
            OPTIONAL MATCH (s)-[:AT_LEVEL]->(l:Level)
            OPTIONAL MATCH (c:Curriculum)
            WHERE c.level = l.name AND (c)-[:MATCHES_INTEREST]->(i)
            RETURN s.name as studentName,
                   l.name as level,
                   collect(DISTINCT i.name) as interests,
                   collect(DISTINCT {
                       title: c.title,
                       description: c.description,
                       topics: c.topics,
                       duration: c.duration_weeks
                   }) as recommendations
        `;

        const results = await this.query(query, { studentId });
        return results.length > 0 ? results[0] : null;
    }

    /**
     * Check proxy health
     * @returns {Promise<boolean>} True if healthy
     */
    async checkHealth() {
        try {
            const response = await fetch('http://127.0.0.1:3939/health');
            const data = await response.json();
            return data.ok === true;
        } catch (error) {
            return false;
        }
    }
}

// Export for use in HTML
const neo4jClient = new Neo4jClient();
