// ATGCO-IDS Simulation and UI Controllers
document.addEventListener("DOMContentLoaded", () => {
    // 1. DATA AND STATES
    const nodes = [
        { id: "Router_0", label: "Gateway Router", x: 300, y: 180, r: 12, trust: 0.99, state: "Benign", logits: [2.5, -1.2, -0.4, -2.1] },
        { id: "Switch_A", label: "Switch Alpha", x: 180, y: 150, r: 9, trust: 0.95, state: "Benign", logits: [1.8, -0.8, -0.2, -1.9] },
        { id: "Switch_B", label: "Switch Beta", x: 420, y: 150, r: 9, trust: 0.94, state: "Benign", logits: [1.7, -0.9, -0.3, -1.8] },
        { id: "Server_1", label: "Web Server", x: 300, y: 80, r: 10, trust: 0.97, state: "Benign", logits: [2.1, -1.0, -0.1, -2.0] },
        { id: "Host_01", label: "Host 01 (Database)", x: 90, y: 80, r: 7, trust: 0.92, state: "Benign", logits: [1.4, -0.5, 0.1, -1.5] },
        { id: "Host_02", label: "Host 02 (Finance)", x: 90, y: 220, r: 7, trust: 0.94, state: "Benign", logits: [1.5, -0.6, 0.0, -1.6] },
        { id: "Host_03", label: "Host 03 (HR Client)", x: 180, y: 260, r: 7, trust: 0.88, state: "Benign", logits: [1.2, -0.4, 0.2, -1.4] },
        { id: "Host_04", label: "Host 04 (Marketing)", x: 420, y: 260, r: 7, trust: 0.85, state: "Benign", logits: [1.1, -0.3, 0.3, -1.3] },
        { id: "Host_05", label: "Host 05 (Dev Client)", x: 510, y: 220, r: 7, trust: 0.91, state: "Benign", logits: [1.3, -0.5, 0.1, -1.5] },
        { id: "Host_06", label: "Host 06 (Guest WiFi)", x: 510, y: 80, r: 7, trust: 0.74, state: "Benign", logits: [0.9, -0.1, 0.5, -1.1] }
    ];

    const links = [
        { source: "Router_0", target: "Server_1" },
        { source: "Router_0", target: "Switch_A" },
        { source: "Router_0", target: "Switch_B" },
        { source: "Switch_A", target: "Host_01" },
        { source: "Switch_A", target: "Host_02" },
        { source: "Switch_A", target: "Host_03" },
        { source: "Switch_B", target: "Host_04" },
        { source: "Switch_B", target: "Host_05" },
        { source: "Switch_B", target: "Host_06" },
        { source: "Host_01", target: "Host_02" },
        { source: "Host_04", target: "Host_05" }
    ];

    let selectedNodeId = null;
    let isSimRunning = true;
    let simSpeed = 1;
    let simTimer = null;
    
    // UI Elements References
    const headerTime = document.getElementById("header-time");
    const globalTrustGauge = document.getElementById("global-trust-gauge");
    const globalTrustVal = document.getElementById("global-trust-val");
    const consensusGauge = document.getElementById("consensus-gauge");
    const consensusVal = document.getElementById("consensus-val");
    const f1ScoreVal = document.getElementById("f1-score-val");
    const fprVal = document.getElementById("fpr-val");
    
    const inspectorPlaceholder = document.getElementById("inspector-placeholder");
    const inspectorContent = document.getElementById("inspector-content");
    const inspectNodeId = document.getElementById("inspect-node-id");
    const inspectNodeState = document.getElementById("inspect-node-state");
    const inspectNodeTrust = document.getElementById("inspect-node-trust");
    const inspectNodeLogits = document.getElementById("inspect-node-logits");
    
    const btnIsolate = document.getElementById("btn-isolate");
    const btnResetTrust = document.getElementById("btn-reset-trust");
    const btnToggleSim = document.getElementById("btn-toggle-sim");
    const btnInjectAttack = document.getElementById("btn-inject-attack");
    const btnClearLogs = document.getElementById("btn-clear-logs");
    
    const terminalStream = document.getElementById("terminal-stream");
    const svgContainer = document.getElementById("svg-host-canvas");

    // 2. INIT SYSTEM
    updateClock();
    setInterval(updateClock, 1000);
    renderTopology();
    addTerminalLog("System Initialized. Active Trust Graph Consensus Optimization (ATGCO) is running.", "info");
    addTerminalLog("Graph Episodic Memory loaded with 117 train snapshots, capacity=1000.", "info");
    addTerminalLog("Ready for network flow monitoring.", "info");
    
    // Start metric update loop
    startMetricUpdates();

    // 3. TAB CONTROLLER
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            const tabId = btn.getAttribute("data-tab");
            document.querySelectorAll(".tab-content").forEach(content => {
                content.classList.add("hidden");
            });
            document.getElementById(`tab-${tabId}`).classList.remove("hidden");
        });
    });

    // 4. SPEED MULTIPLIER CONTROLLER
    const speedOpts = document.querySelectorAll(".speed-opt");
    speedOpts.forEach(opt => {
        opt.addEventListener("click", () => {
            speedOpts.forEach(o => o.classList.remove("active"));
            opt.classList.add("active");
            simSpeed = parseInt(opt.getAttribute("data-speed"));
            addTerminalLog(`Simulation speed multiplier changed to ${simSpeed}x`, "info");
            
            // Restart simulator loop with new speed
            if (isSimRunning) {
                stopMetricUpdates();
                startMetricUpdates();
            }
        });
    });

    // 5. GRAPH RENDERING (SVG CANVAS)
    function renderTopology() {
        svgContainer.innerHTML = ""; // Clear
        const width = svgContainer.clientWidth;
        const height = svgContainer.clientHeight || 300;
        
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("class", "topology-svg");
        svg.setAttribute("viewBox", `0 0 600 300`);

        // Draw Links (Lines)
        links.forEach(link => {
            const sourceNode = nodes.find(n => n.id === link.source);
            const targetNode = nodes.find(n => n.id === link.target);
            if (sourceNode && targetNode) {
                const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                line.setAttribute("x1", sourceNode.x);
                line.setAttribute("y1", sourceNode.y);
                line.setAttribute("x2", targetNode.x);
                line.setAttribute("y2", targetNode.y);
                
                let linkClass = "link";
                if (selectedNodeId === sourceNode.id || selectedNodeId === targetNode.id) {
                    linkClass += " active";
                }
                line.setAttribute("class", linkClass);
                svg.appendChild(line);
            }
        });

        // Draw Nodes (Circles & Labels)
        nodes.forEach(node => {
            const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
            let nodeClass = "node";
            if (selectedNodeId === node.id) {
                nodeClass += " selected";
            }
            group.setAttribute("class", nodeClass);
            group.setAttribute("id", `svg-node-${node.id}`);
            
            // Circle
            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("cx", node.x);
            circle.setAttribute("cy", node.y);
            circle.setAttribute("r", node.r);
            
            let circleClass = "node-circle";
            if (node.state === "Suspect") {
                circleClass += " suspect";
            } else if (node.state === "Isolated") {
                circleClass += " isolated";
            }
            circle.setAttribute("class", circleClass);
            
            // Label
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", node.x);
            text.setAttribute("y", node.y + node.r + 12);
            text.setAttribute("class", "node-label");
            text.textContent = node.id;
            
            group.appendChild(circle);
            group.appendChild(text);
            
            // Click listener
            group.addEventListener("click", (e) => {
                e.stopPropagation();
                selectNode(node.id);
            });
            
            svg.appendChild(group);
        });

        svgContainer.appendChild(svg);
    }

    // 6. NODE SELECTION
    function selectNode(id) {
        selectedNodeId = id;
        renderTopology(); // Redraw with highlights
        
        const node = nodes.find(n => n.id === id);
        if (node) {
            inspectorPlaceholder.classList.add("hidden");
            inspectorContent.classList.remove("hidden");
            
            inspectNodeId.textContent = `${node.id} (${node.label})`;
            inspectNodeState.textContent = node.state;
            
            // Reset class
            inspectNodeState.className = "status-badge";
            if (node.state === "Benign") {
                inspectNodeState.classList.add("state-benign");
            } else if (node.state === "Suspect") {
                inspectNodeState.classList.add("state-suspect");
            } else if (node.state === "Isolated") {
                inspectNodeState.classList.add("state-isolated");
            }
            
            inspectNodeTrust.textContent = node.trust.toFixed(4);
            inspectNodeLogits.textContent = `[${node.logits.map(l => l.toFixed(2)).join(", ")}]`;
        }
    }

    // Unselect node clicking on canvas background
    svgContainer.addEventListener("click", () => {
        selectedNodeId = null;
        renderTopology();
        inspectorContent.classList.add("hidden");
        inspectorPlaceholder.classList.remove("hidden");
    });

    // 7. MITIGATION ACTIONS
    btnIsolate.addEventListener("click", () => {
        if (!selectedNodeId) return;
        const node = nodes.find(n => n.id === selectedNodeId);
        if (node) {
            node.state = "Isolated";
            node.trust = 0.05;
            node.logits = [-2.1, -1.8, -0.4, 3.2]; // High intrusion logits
            selectNode(selectedNodeId);
            
            addTerminalLog(`MANUAL OVERRIDE: Host isolation triggered for ${node.id}.`, "danger");
            addTerminalLog(`[SIEM ALERT] Port Block applied at Firewall border to host ${node.id} (trust score minimized to 0.05).`, "warning");
        }
    });

    btnResetTrust.addEventListener("click", () => {
        if (!selectedNodeId) return;
        const node = nodes.find(n => n.id === selectedNodeId);
        if (node) {
            node.state = "Benign";
            node.trust = 0.90;
            node.logits = [1.9, -0.8, -0.2, -1.8]; // Reset to healthy normal
            selectNode(selectedNodeId);
            
            addTerminalLog(`MANUAL OVERRIDE: Trust score reset to healthy for ${node.id}.`, "info");
            addTerminalLog(`[SIEM ALERT] Isolated state cleared. Host ${node.id} reintroduced to consensus routing.`, "info");
        }
    });

    // 8. SIMULATION RUN LOOPS
    btnToggleSim.addEventListener("click", () => {
        isSimRunning = !isSimRunning;
        if (isSimRunning) {
            btnToggleSim.textContent = "Pause Simulation";
            btnToggleSim.classList.remove("btn-secondary");
            btnToggleSim.classList.add("btn-primary");
            startMetricUpdates();
            addTerminalLog("Simulation resumed.", "info");
        } else {
            btnToggleSim.textContent = "Resume Simulation";
            btnToggleSim.classList.remove("btn-primary");
            btnToggleSim.classList.add("btn-secondary");
            stopMetricUpdates();
            addTerminalLog("Simulation paused.", "warning");
        }
    });

    btnInjectAttack.addEventListener("click", () => {
        // Select a random benign node to attack
        const benignNodes = nodes.filter(n => n.state === "Benign" && n.id !== "Router_0");
        if (benignNodes.length === 0) {
            addTerminalLog("All hosts currently flagged. Reset trust scores first.", "warning");
            return;
        }
        
        const target = benignNodes[Math.floor(Math.random() * benignNodes.length)];
        
        // Phase 1: Attack detected (Suspect)
        target.state = "Suspect";
        target.trust = 0.32;
        target.logits = [0.2, 0.4, 2.1, -0.8]; // Anomaly logits
        if (selectedNodeId === target.id) {
            selectNode(target.id);
        }
        renderTopology();
        
        addTerminalLog(`[ATGCO ALARM] Anomaly flagged on host ${target.id} (trust dropped to 0.32).`, "warning");
        addTerminalLog(`[SIEM MITIGATION] GCO Jacobi consensus relaxation initialized. Evaluating neighbor logit variances...`, "info");
        
        // Phase 2: Consensus reached, isolate (1.5s delay / adjusted by sim speed)
        setTimeout(() => {
            target.state = "Isolated";
            target.trust = 0.05;
            target.logits = [-2.5, -1.9, -0.3, 3.4]; // Locked
            
            if (selectedNodeId === target.id) {
                selectNode(target.id);
            }
            renderTopology();
            
            addTerminalLog(`[SIEM MITIGATION] Consensus convergence verified: Host ${target.id} is isolated. Border firewall updated to block ingress/egress.`, "danger");
        }, 1500 / simSpeed);
    });

    btnClearLogs.addEventListener("click", () => {
        terminalStream.innerHTML = "";
    });

    // 9. UPDATE METRIC SIMULATION LOOP
    function startMetricUpdates() {
        const intervalMs = 2000 / simSpeed;
        simTimer = setInterval(() => {
            // Jitter metrics slightly
            const meanTrust = nodes.reduce((acc, n) => acc + n.trust, 0) / nodes.length;
            const consensusRate = 0.90 + Math.random() * 0.09 - (nodes.filter(n => n.state === "Isolated").length * 0.02);
            
            updateRadialGauge(globalTrustGauge, globalTrustVal, meanTrust, 1);
            updateRadialGauge(consensusGauge, consensusVal, consensusRate * 100, "%");
            
            // Jitter F1 and FPR slightly
            const jitteredF1 = 75.6 + (Math.random() * 0.4 - 0.2);
            f1ScoreVal.textContent = `${jitteredF1.toFixed(1)}%`;
            
            // Random dummy network traffic log
            if (Math.random() > 0.4) {
                const randomNode = nodes[Math.floor(Math.random() * nodes.length)];
                addTerminalLog(`Flow packet vector processed for ${randomNode.id} - Trust state healthy.`, "log-time");
            }
        }, intervalMs);
    }

    function stopMetricUpdates() {
        if (simTimer) {
            clearInterval(simTimer);
        }
    }

    // Radial gauge renderer helper
    function updateRadialGauge(gaugeElement, valElement, value, unit) {
        valElement.textContent = typeof value === "number" && value < 1 ? value.toFixed(2) : `${Math.round(value)}${unit}`;
        
        // Map value to dash offset: r=40, circum=251
        // Value 100% -> offset 0. Value 0% -> offset 251.
        const percent = typeof value === "number" && value <= 1 ? value : value / 100;
        const offset = 251 - (251 * percent);
        gaugeElement.style.strokeDashoffset = offset;
        
        // Color update based on score
        if (percent > 0.8) {
            gaugeElement.style.stroke = "var(--neon-cyan)";
        } else if (percent > 0.5) {
            gaugeElement.style.stroke = "var(--neon-orange)";
        } else {
            gaugeElement.style.stroke = "var(--neon-magenta)";
        }
    }

    // Terminal Logger
    function addTerminalLog(message, type) {
        const timeStr = getFormattedTime();
        const logEntry = document.createElement("div");
        logEntry.className = "log-entry";
        
        let typeClass = "";
        if (type === "info") typeClass = "log-info";
        else if (type === "warning") typeClass = "log-warning";
        else if (type === "danger") typeClass = "log-danger";
        else typeClass = "log-time";
        
        logEntry.innerHTML = `<span class="log-time">[${timeStr}]</span> <span class="${typeClass}">${message}</span>`;
        terminalStream.appendChild(logEntry);
        
        // Auto scroll
        terminalStream.scrollTop = terminalStream.scrollHeight;
    }

    // Clock helpers
    function updateClock() {
        headerTime.textContent = getFormattedTime(true);
    }

    function getFormattedTime(includeDate = false) {
        const now = new Date();
        const hrs = String(now.getHours()).padStart(2, '0');
        const mins = String(now.getMinutes()).padStart(2, '0');
        const secs = String(now.getSeconds()).padStart(2, '0');
        
        if (includeDate) {
            const yy = now.getFullYear();
            const mm = String(now.getMonth() + 1).padStart(2, '0');
            const dd = String(now.getDate()).padStart(2, '0');
            return `${yy}-${mm}-${dd} ${hrs}:${mins}:${secs}`;
        }
        return `${hrs}:${mins}:${secs}`;
    }
});
