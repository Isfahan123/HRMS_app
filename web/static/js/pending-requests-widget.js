/**
 * Pending Requests Dashboard Widget
 * Displays a summary of items requiring admin attention
 */

class PendingRequestsWidget {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container ${containerId} not found`);
            return;
        }
        
        this.data = {
            leave_requests: 0,
            bonus_pending: 0,
            engagements_pending: 0,
            total: 0
        };
        
        this.init();
    }
    
    init() {
        this.render();
        this.loadData();
        
        // Auto-refresh every 5 minutes
        setInterval(() => this.loadData(), 5 * 60 * 1000);
    }
    
    render() {
        this.container.innerHTML = `
            <div class="pending-requests-widget" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 12px; padding: 20px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="margin: 0; font-size: 18px; font-weight: 600;">
                        🔔 Pending Approvals
                    </h3>
                    <div id="pendingTotalBadge" style="background: rgba(255,255,255,0.3); 
                            padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 16px;">
                        <span id="pendingTotalCount">...</span>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px;">
                    <!-- Leave Requests Card -->
                    <div class="pending-card" onclick="navigateToLeaveRequests()" 
                         style="background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); 
                                border-radius: 8px; padding: 15px; cursor: pointer; transition: all 0.3s ease;"
                         onmouseover="this.style.background='rgba(255,255,255,0.25)'; this.style.transform='translateY(-2px)'"
                         onmouseout="this.style.background='rgba(255,255,255,0.15)'; this.style.transform='translateY(0)'">
                        <div style="font-size: 28px; margin-bottom: 8px;">📬</div>
                        <div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;" id="leaveRequestsCount">-</div>
                        <div style="font-size: 13px; opacity: 0.9;">Leave Requests</div>
                    </div>
                    
                    <!-- Bonuses Card -->
                    <div class="pending-card" onclick="navigateToBonuses()" 
                         style="background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); 
                                border-radius: 8px; padding: 15px; cursor: pointer; transition: all 0.3s ease;"
                         onmouseover="this.style.background='rgba(255,255,255,0.25)'; this.style.transform='translateY(-2px)'"
                         onmouseout="this.style.background='rgba(255,255,255,0.15)'; this.style.transform='translateY(0)'">
                        <div style="font-size: 28px; margin-bottom: 8px;">💰</div>
                        <div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;" id="bonusesPendingCount">-</div>
                        <div style="font-size: 13px; opacity: 0.9;">Pending Bonuses</div>
                    </div>
                    
                    <!-- Engagements Card -->
                    <div class="pending-card" onclick="navigateToEngagements()" 
                         style="background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); 
                                border-radius: 8px; padding: 15px; cursor: pointer; transition: all 0.3s ease;"
                         onmouseover="this.style.background='rgba(255,255,255,0.25)'; this.style.transform='translateY(-2px)'"
                         onmouseout="this.style.background='rgba(255,255,255,0.15)'; this.style.transform='translateY(0)'">
                        <div style="font-size: 28px; margin-bottom: 8px;">📚</div>
                        <div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;" id="engagementsPendingCount">-</div>
                        <div style="font-size: 13px; opacity: 0.9;">Engagement Requests</div>
                    </div>
                </div>
                
                <!-- Last Updated -->
                <div style="text-align: right; margin-top: 15px; font-size: 11px; opacity: 0.7;">
                    Last updated: <span id="pendingLastUpdate">-</span>
                </div>
                
                <!-- Refresh Button -->
                <div style="text-align: center; margin-top: 10px;">
                    <button onclick="window.pendingRequestsWidget.loadData()" 
                            style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); 
                                   color: white; padding: 8px 20px; border-radius: 6px; cursor: pointer; 
                                   font-size: 12px; transition: all 0.3s ease;"
                            onmouseover="this.style.background='rgba(255,255,255,0.3)'"
                            onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                        🔄 Refresh
                    </button>
                </div>
            </div>
        `;
    }
    
    async loadData() {
        try {
            // Load leave requests
            const leaveResponse = await fetch('/api/admin/leave-requests');
            const leaveData = await leaveResponse.json();
            if (leaveData.success && leaveData.data) {
                const pendingLeaves = leaveData.data.filter(req => req.status === 'pending');
                this.data.leave_requests = pendingLeaves.length;
            }
            
            // Load bonuses
            const bonusResponse = await fetch('/api/admin/bonuses');
            const bonusData = await bonusResponse.json();
            if (bonusData.success && bonusData.data) {
                const pendingBonuses = bonusData.data.filter(b => b.status === 'pending');
                this.data.bonus_pending = pendingBonuses.length;
            }
            
            // Load engagements
            const engResponse = await fetch('/api/admin/engagements/all');
            const engData = await engResponse.json();
            if (engData.success && engData.data) {
                const pendingEngagements = engData.data.filter(e => e.status === 'pending');
                this.data.engagements_pending = pendingEngagements.length;
            }
            
            // Calculate total
            this.data.total = this.data.leave_requests + this.data.bonus_pending + this.data.engagements_pending;
            
            // Update UI
            this.updateUI();
            
        } catch (error) {
            console.error('Error loading pending requests:', error);
            this.showError();
        }
    }
    
    updateUI() {
        // Update counts
        document.getElementById('leaveRequestsCount').textContent = this.data.leave_requests;
        document.getElementById('bonusesPendingCount').textContent = this.data.bonus_pending;
        document.getElementById('engagementsPendingCount').textContent = this.data.engagements_pending;
        document.getElementById('pendingTotalCount').textContent = this.data.total;
        
        // Update timestamp
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        document.getElementById('pendingLastUpdate').textContent = timeStr;
        
        // Add badge animation if there are pending items
        if (this.data.total > 0) {
            const badge = document.getElementById('pendingTotalBadge');
            badge.style.animation = 'pulse 2s infinite';
            
            // Add pulse animation if not already added
            if (!document.getElementById('pulseAnimation')) {
                const style = document.createElement('style');
                style.id = 'pulseAnimation';
                style.textContent = `
                    @keyframes pulse {
                        0%, 100% { transform: scale(1); }
                        50% { transform: scale(1.05); }
                    }
                `;
                document.head.appendChild(style);
            }
        }
    }
    
    showError() {
        document.getElementById('leaveRequestsCount').textContent = '?';
        document.getElementById('bonusesPendingCount').textContent = '?';
        document.getElementById('engagementsPendingCount').textContent = '?';
        document.getElementById('pendingTotalCount').textContent = '!';
        document.getElementById('pendingLastUpdate').textContent = 'Error';
    }
}

// Navigation helper functions
function navigateToLeaveRequests() {
    // Switch to Leaves tab and Pending subtab
    const leaveTab = document.querySelector('[data-tab="leaves"]');
    if (leaveTab) {
        leaveTab.click();
        setTimeout(() => {
            const pendingSubtab = document.querySelector('[data-subtab="leavePending"]');
            if (pendingSubtab) pendingSubtab.click();
        }, 100);
    }
}

function navigateToBonuses() {
    // Switch to Payroll tab and Bonuses subtab
    const payrollTab = document.querySelector('[data-tab="payroll"]');
    if (payrollTab) {
        payrollTab.click();
        setTimeout(() => {
            const bonusesSubtab = document.querySelector('[data-subtab="payrollBonuses"]');
            if (bonusesSubtab) bonusesSubtab.click();
        }, 100);
    }
}

function navigateToEngagements() {
    // Switch to Activities tab
    const activitiesTab = document.querySelector('[data-tab="activities"]');
    if (activitiesTab) {
        activitiesTab.click();
    }
}

// Initialize widget when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on admin dashboard
    if (document.getElementById('pendingRequestsWidget')) {
        window.pendingRequestsWidget = new PendingRequestsWidget('pendingRequestsWidget');
    }
});
