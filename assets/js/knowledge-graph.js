/**
 * Soo Edu Knowledge Graph Visualization
 * Interactive visualization of the Soo Edu second brain
 * Powered by vis.js and daily Neo4j snapshots
 */

class KnowledgeGraphViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.network = null;
        this.data = null;
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

        // vis.js network options
        const options = {
            nodes: {
                font: {
                    size: 14,
                    face: 'Inter, -apple-system, sans-serif',
                    color: '#ffffff'
                },
                borderWidth: 2,
                borderWidthSelected: 4,
                shadow: {
                    enabled: true,
                    color: 'rgba(0,0,0,0.2)',
                    size: 10,
                    x: 0,
                    y: 0
                }
            },
            edges: {
                font: {
                    size: 12,
                    align: 'middle',
                    color: '#666666',
                    background: 'rgba(255,255,255,0.8)'
                },
                color: {
                    color: '#848484',
                    highlight: '#2196F3',
                    hover: '#2196F3'
                },
                width: 2,
                smooth: {
                    type: 'continuous',
                    roundness: 0.5
                },
                arrows: {
                    to: {
                        enabled: true,
                        scaleFactor: 0.5
                    }
                }
            },
            physics: {
                enabled: true,
                forceAtlas2Based: {
                    gravitationalConstant: -50,
                    centralGravity: 0.01,
                    springConstant: 0.08,
                    springLength: 100,
                    damping: 0.4,
                    avoidOverlap: 0
                },
                maxVelocity: 50,
                minVelocity: 0.1,
                solver: 'forceAtlas2Based',
                stabilization: {
                    enabled: true,
                    iterations: 1000,
                    updateInterval: 100,
                    onlyDynamicEdges: false,
                    fit: true
                },
                timestep: 0.5,
                adaptiveTimestep: true
            },
            interaction: {
                hover: true,
                tooltipDelay: 100,
                navigationButtons: true,
                keyboard: true,
                zoomView: true,
                dragView: true,
                hideEdgesOnDrag: true,
                hideNodesOnDrag: false
            },
            layout: {
                improvedLayout: true,
                randomSeed: 42
            }
        };

        // Create network
        this.network = new vis.Network(
            this.container,
            {
                nodes: new vis.DataSet(this.data.nodes),
                edges: new vis.DataSet(this.data.edges)
            },
            options
        );

        // Event listeners
        this.setupEventListeners();

        // Show metadata
        this.showMetadata();
    }

    setupEventListeners() {
        // Node click event
        this.network.on('click', (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                this.showNodeDetails(nodeId);
            }
        });

        // Stabilization progress
        this.network.on('stabilizationProgress', (params) => {
            const progress = Math.round((params.iterations / params.total) * 100);
            this.updateLoadingProgress(progress);
        });

        // Stabilization done
        this.network.on('stabilizationIterationsDone', () => {
            this.hideLoading();
            this.network.setOptions({ physics: { enabled: false } }); // Stop physics after load to save CPU
        });

        // Re-enable physics on drag start so nodes move naturally
        this.network.on("dragStart", (params) => {
            this.network.setOptions({ physics: { enabled: true } });
        });

        // Disable physics again on drag end
        this.network.on("dragEnd", (params) => {
            this.network.setOptions({ physics: { enabled: false } });
        });
    }

    showNodeDetails(nodeId) {
        const node = this.data.nodes.find(n => n.id === nodeId);
        if (!node) return;

        const detailsHtml = `
            <div class="node-details-popup">
                <h4>${node.label}</h4>
                <p><strong>유형:</strong> ${node.group}</p>
                ${Object.entries(node.properties || {})
                .map(([key, value]) => `<p><strong>${key}:</strong> ${value}</p>`)
                .join('')}
            </div>
        `;

        // Show in tooltip or modal
        console.log('Node details:', node);
    }

    showMetadata() {
        const meta = this.data.metadata;
        const metaElement = document.getElementById('graph-metadata');

        if (metaElement) {
            metaElement.innerHTML = `
                <div class="graph-stats">
                    <span><strong>노드:</strong> ${meta.node_count}개</span>
                    <span><strong>연결:</strong> ${meta.edge_count}개</span>
                    <span><strong>마지막 업데이트:</strong> ${new Date(meta.generated_at).toLocaleDateString('ko-KR')}</span>
                </div>
            `;
        }
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="graph-error">
                <p>⚠️ ${message}</p>
                <p style="font-size: 0.9rem; color: #666;">Neo4j 데이터가 아직 생성되지 않았거나 프록시 서버가 실행 중이지 않습니다.</p>
            </div>
        `;
    }

    updateLoadingProgress(progress) {
        const loadingElement = document.getElementById('graph-loading');
        if (loadingElement) {
            loadingElement.innerHTML = `<p>그래프 생성 중... ${progress}%</p>`;
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
            <div id="graph-loading" class="graph-loading">
                <p>지식 그래프 로딩 중...</p>
            </div>
        `;

        // Load data
        const success = await this.loadData();

        if (success) {
            // Render graph
            this.render();
        }
    }
}

// Auto-initialize when vis.js is loaded
window.KnowledgeGraphViewer = KnowledgeGraphViewer;
