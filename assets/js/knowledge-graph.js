/**
 * Soo Edu Knowledge Graph Visualization (3D Version)
 * Interactive 3D visualization of the Soo Edu second brain
 * Powered by 3d-force-graph
 */

class KnowledgeGraphViewer {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.graph = null;
        this.data = null;
        this.isRotationActive = true;
    }

    async loadData() {
        try {
            // Use relative path that works with Jekyll's baseurl
            const baseUrl = document.querySelector('base')?.href || window.location.origin + window.location.pathname.split('/').slice(0, -1).join('/');
            const jsonPath = baseUrl.includes('sooedu-blog')
                ? '/sooedu-blog/assets/data/knowledge-graph-latest.json'
                : '/assets/data/knowledge-graph-latest.json';

            const response = await fetch(jsonPath);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            this.data = await response.json();
            return true;
        } catch (error) {
            console.error('Failed to load knowledge graph:', error);
            this.showError('지식 그래프 데이터를 불러올 수 없습니다.');
            return false;
        }
    }

    render() {
        if (!this.data) {
            console.error('No data to render');
            return;
        }

        // Color mapping
        const colorMap = {
            "Student": "#4CAF50",      // Green
            "Word": "#9C27B0",         // Purple
            "Book": "#F44336",         // Red
            "Interest": "#FF9800",     // Orange
            "Level": "#2196F3",        // Blue
            "Lesson": "#00BCD4"        // Cyan
        };

        // Prepare data for 3d-force-graph
        // Ensure IDs are strings to avoid any type mismatch issues in d3-force
        const gData = {
            nodes: this.data.nodes.map(node => ({
                id: String(node.id),
                name: node.label,
                group: node.group,
                val: (node.size || 10) * 0.5, // adjust size scale
                color: colorMap[node.group] || "#ffffff",
                ...node.properties
            })),
            links: this.data.edges.map(edge => ({
                source: String(edge.from),
                target: String(edge.to),
                label: edge.label,
                ...edge.properties
            }))
        };

        // Initialize 3D Graph
        this.graph = ForceGraph3D()
            (this.container)
            .graphData(gData)
            .backgroundColor('#000011') // Deep space blue/black
            .nodeLabel('name')
            .nodeColor('color')
            .nodeResolution(16) // Sphere smoothness
            .linkColor(() => 'rgba(255, 255, 255, 0.2)') // Faint white lines
            .linkWidth(1)
            .linkDirectionalParticles(2) // Flowing particles for "active" look
            .linkDirectionalParticleWidth(1.5)
            .linkDirectionalParticleSpeed(0.005)
            .nodeThreeObjectExtend(true) // Extend node object with custom geometry if needed, but here we stick to default spheres

            // Interaction
            .onNodeClick(node => {
                // Focus on node
                const distance = 40;
                const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);

                this.graph.cameraPosition(
                    { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }, // new position
                    node, // lookAt ({ x, y, z })
                    3000  // ms transition duration
                );

                this.showNodeDetails(node);

                // Pause rotation on interaction
                this.isRotationActive = false;
            })
            .onNodeHover(node => {
                this.container.style.cursor = node ? 'pointer' : null;
                this.isRotationActive = !node; // Pause rotation when hovering a node
            });

        // Force zoom to fit after a short delay to allow physics to settle slightly
        setTimeout(() => {
            if (this.graph) {
                this.graph.zoomToFit(1000, 100); // duration, padding
            }
        }, 1000);

        // Add auto-rotation
        this.videoRotate();

        // Adjust canvas size to match container
        this.resize();
        window.addEventListener('resize', () => this.resize());

        // Show metadata
        this.showMetadata();
        this.hideLoading();
    }

    videoRotate() {
        // Slow rotation relative to the camera
        let angle = 0;
        setInterval(() => {
            if (this.graph && this.isRotationActive) {
                angle += 0.001; // Rotation speed
                this.graph.cameraPosition({
                    x: 200 * Math.sin(angle),
                    z: 200 * Math.cos(angle)
                });
            }
        }, 10);
    }

    resize() {
        if (this.graph) {
            // Get dimensions from parent container or window
            const width = this.container.clientWidth || window.innerWidth;
            const height = this.container.clientHeight || 500; // Default height if 0
            this.graph.width(width);
            this.graph.height(height);
        }
    }

    showNodeDetails(node) {
        // Simple console log for now, can be expanded to UI overlay
        console.log('Node Selected:', node);
        // You would update a DOM element here with node details

        // Example fallback: show simple alert or update a specific div if it exists
        const detailContainer = document.querySelector('.node-details-popup');
        if (detailContainer) {
            detailContainer.innerHTML = `
                <h4>${node.name}</h4>
                <p>Type: ${node.group}</p>
            `;
            detailContainer.style.display = 'block';
        }
    }

    showMetadata() {
        const meta = this.data.metadata;
        const metaElement = document.getElementById('graph-metadata');

        if (metaElement) {
            // Updated style for dark background
            metaElement.style.color = '#cccccc';
            metaElement.innerHTML = `
                <div class="graph-stats">
                    <span style="margin-right: 10px;"><strong>Nodes:</strong> ${meta.node_count}</span>
                    <span style="margin-right: 10px;"><strong>Links:</strong> ${meta.edge_count}</span>
                    <span><strong>Updated:</strong> ${new Date(meta.generated_at).toLocaleDateString('ko-KR')}</span>
                </div>
            `;
        }
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="graph-error" style="color: white; text-align: center; padding-top: 50px;">
                <p>⚠️ ${message}</p>
                <p style="font-size: 0.9rem; opacity: 0.7;">데이터 로드 실패</p>
            </div>
        `;
    }

    updateLoadingProgress(progress) {
        const loadingElement = document.getElementById('graph-loading');
        if (loadingElement) {
            loadingElement.innerHTML = `<p>Loading Cosmic Brain... ${progress}%</p>`;
        }
    }

    hideLoading() {
        const loadingElement = document.getElementById('graph-loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    async init() {
        // Show loading
        this.container.innerHTML = `
            <div id="graph-loading" class="graph-loading" style="color: white; display: flex; justify-content: center; align-items: center; height: 100%; font-family: monospace;">
                <p>🧠 Initializing Soo Edu Neural Network...</p>
            </div>
        `;

        // Load data
        const success = await this.loadData();

        if (success) {
            // Clear loading text
            this.container.innerHTML = '';
            // Render graph
            this.render();
        }
    }
}

// Auto-initialize
window.KnowledgeGraphViewer = KnowledgeGraphViewer;
