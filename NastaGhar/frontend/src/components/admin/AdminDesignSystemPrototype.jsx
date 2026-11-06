import { useState } from 'react';
import './AdminDesignSystem.css';
import { AdminSidebar } from './AdminSidebar';
import { AdminHeader } from './AdminHeader';
import { AdminCard } from './common/AdminCard';
import { AdminKpi } from './common/AdminKpi';
import { AdminLineChart, AdminBarChart, AdminDonutChart } from './common/AdminCharts';
import { AdminTable } from './common/AdminTable';
import { AdminButton, AdminInput, AdminSelect, AdminSegmentedControl } from './common/AdminControls';
import { AdminBadge, StatusBadge, EntitlementBadge } from './common/AdminBadge';
import { AdminNotification } from './common/AdminNotification';
import { AdminModal, AdminConfirmDialog } from './common/AdminModal';

/**
 * VRAJA AI Super Admin Design System Prototype & Visual Showcase
 * STEP 1: Interactive Design System Prototype
 */
export default function AdminDesignSystemPrototype({ onBackToLiveAdmin }) {
  // Shell Layout State
  const [activeTab, setActiveTab] = useState('design-system');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Interactive Prototype State
  const [activeSegment, setActiveSegment] = useState('all');
  const [demoInput, setDemoInput] = useState('');
  const [demoSelect, setDemoSelect] = useState('active');
  const [selectedTableKeys, setSelectedTableKeys] = useState(['t-01']);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [activeNotification, setActiveNotification] = useState({
    show: true,
    type: 'success',
    title: 'Design System Verified',
    message: 'Official VRAJA AI corporate tokens active: Warm Ivory, Deep Emerald, Muted Gold, Forest Charcoal.',
  });

  // Design-only demonstration datasets (clearly labelled placeholders)
  const demoKpiData = [
    {
      label: 'Active Platform Tenants',
      value: '24',
      trend: '12.5%',
      trendDirection: 'positive',
      subtext: 'Design-only placeholder metric',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z" />
          <path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2" />
        </svg>
      ),
    },
    {
      label: 'Review Assistants (Product A)',
      value: '22',
      trend: '8.3%',
      trendDirection: 'positive',
      subtext: '91.6% tenant coverage',
      goldIcon: true,
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      ),
    },
    {
      label: 'Digital Cards (Product B)',
      value: '18',
      trend: 'Neutral',
      trendDirection: 'neutral',
      subtext: '75.0% tenant coverage',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect width="20" height="14" x="2" y="5" rx="2" />
          <line x1="2" x2="22" y1="10" y2="10" />
        </svg>
      ),
    },
    {
      label: 'Database Status (WAL)',
      value: '100%',
      trend: 'Healthy',
      trendDirection: 'positive',
      subtext: 'Zero fragmentation • Online',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
          <path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3" />
        </svg>
      ),
    },
  ];

  const demoLineData = [
    { label: 'Jan', value: 12 },
    { label: 'Feb', value: 16 },
    { label: 'Mar', value: 19 },
    { label: 'Apr', value: 24 },
    { label: 'May', value: 31 },
    { label: 'Jun', value: 38 },
    { label: 'Jul', value: 45 },
  ];

  const demoBarData = [
    { label: '08:00', value: 15 },
    { label: '10:00', value: 42 },
    { label: '12:00', value: 95 },
    { label: '14:00', value: 88 },
    { label: '16:00', value: 50 },
    { label: '18:00', value: 78 },
    { label: '20:00', value: 110 },
  ];

  const demoDonutData = [
    { label: 'Full Suite (A + B)', count: 18, color: '#174D3A' },
    { label: 'Review Only (A)', count: 4, color: '#C6A66B' },
    { label: 'Digital Card Only (B)', count: 2, color: '#718078' },
  ];

  const demoTableColumns = [
    {
      key: 'name',
      title: 'Tenant / Client',
      sortable: true,
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              backgroundColor: '#DCE5DD',
              color: '#174D3A',
              fontWeight: 700,
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {row.name.substring(0, 2).toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 600, color: '#26352D' }}>{row.name}</div>
            <div style={{ fontSize: '11px', color: '#718078' }}>ID: {row.id}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'category',
      title: 'Category & Branch',
      render: (row) => (
        <div>
          <div>{row.category}</div>
          <div style={{ fontSize: '11px', color: '#718078' }}>{row.branch}</div>
        </div>
      ),
    },
    {
      key: 'entitlements',
      title: 'Active Products',
      render: (row) => (
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {row.entitlements.map((e) => (
            <EntitlementBadge key={e} entitlement={e} />
          ))}
        </div>
      ),
    },
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: 'actions',
      title: 'Actions',
      align: 'right',
      render: () => (
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
          <AdminButton
            variant="outline"
            size="sm"
            onClick={() => setIsModalOpen(true)}
          >
            View
          </AdminButton>
          <AdminButton
            variant="danger"
            size="sm"
            onClick={() => setIsConfirmOpen(true)}
          >
            Suspend
          </AdminButton>
        </div>
      ),
    },
  ];

  const demoTableData = [
    {
      id: 't-01',
      name: 'Nasta Ghar (Flagship)',
      category: 'Breakfast & Snacks',
      branch: 'Main Branch',
      entitlements: ['review_manager', 'digital_card'],
      status: 'active',
    },
    {
      id: 't-02',
      name: 'Cafe Alpha Speciality',
      category: 'Artisanal Cafe',
      branch: 'Downtown Arcade',
      entitlements: ['review_manager', 'digital_card'],
      status: 'active',
    },
    {
      id: 't-03',
      name: 'Green Leaf Bistro',
      category: 'Pure Vegetarian',
      branch: 'Sector 5',
      entitlements: ['review_manager'],
      status: 'active',
    },
    {
      id: 't-04',
      name: 'Royal Heritage Dine',
      category: 'Fine Dining',
      branch: 'Palace Road',
      entitlements: ['digital_card'],
      status: 'suspended',
    },
  ];

  return (
    <div className={`vraja-admin-shell ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      {/* 1. Deep Emerald Left Sidebar */}
      <AdminSidebar
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        isMobileOpen={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
        adminUser={{ display_name: 'Super Admin', email: 'admin@vraja.ai' }}
        onLogout={() => {
          if (onBackToLiveAdmin) onBackToLiveAdmin();
        }}
      />

      {/* 2. Warm Ivory Main Canvas */}
      <div className="vraja-admin-main">
        {/* 4. Premium Top Navigation Header */}
        <AdminHeader
          activeTitle="Design System Prototype (Step 1 Review)"
          breadcrumbs={['VRAJA AI', 'Design System']}
          onOpenMobileMenu={() => setIsMobileMenuOpen(true)}
          adminUser={{ display_name: 'Super Admin', email: 'admin@vraja.ai' }}
          notificationCount={1}
          onOpenNotifications={() =>
            setActiveNotification({
              show: true,
              type: 'info',
              title: 'Design System Notifications',
              message: 'All 11 required enterprise components are rendered below.',
            })
          }
          primaryAction={
            <div style={{ display: 'flex', gap: '8px' }}>
              <AdminButton
                variant="gold"
                size="sm"
                onClick={() => setIsModalOpen(true)}
              >
                + Modal Demo
              </AdminButton>
              {onBackToLiveAdmin && (
                <AdminButton
                  variant="outline"
                  size="sm"
                  onClick={onBackToLiveAdmin}
                >
                  Exit Preview
                </AdminButton>
              )}
            </div>
          }
        />

        {/* Page Content Container */}
        <main className="vraja-page-content">
          {/* Notification Component Banner */}
          {activeNotification.show && (
            <AdminNotification
              type={activeNotification.type}
              title={activeNotification.title}
              message={activeNotification.message}
              onClose={() => setActiveNotification({ ...activeNotification, show: false })}
            />
          )}

          {/* Page Title & Action Bar */}
          <div className="vraja-page-header">
            <div className="vraja-page-title-group">
              <h1 className="vraja-page-title">Enterprise Design System & Component Library</h1>
              <p className="vraja-page-subtitle">
                Official VRAJA AI Corporate System • Warm Ivory, Deep Emerald, Muted Gold & Forest Charcoal
              </p>
            </div>
            <div className="vraja-page-actions">
              <AdminSegmentedControl
                options={[
                  { value: 'all', label: 'All Components' },
                  { value: 'cards', label: 'Cards & KPIs' },
                  { value: 'charts', label: 'Charts' },
                  { value: 'controls', label: 'Forms & Buttons' },
                ]}
                value={activeSegment}
                onChange={setActiveSegment}
              />
            </div>
          </div>

          {/* 5. KPI Metric Cards */}
          {(activeSegment === 'all' || activeSegment === 'cards') && (
            <section>
              <div style={{ marginBottom: '12px', fontSize: '13px', fontWeight: 600, color: '#718078', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                5. KPI Card Components
              </div>
              <div className="vraja-kpi-grid">
                {demoKpiData.map((kpi, idx) => (
                  <AdminKpi
                    key={idx}
                    label={kpi.label}
                    value={kpi.value}
                    trend={kpi.trend}
                    trendDirection={kpi.trendDirection}
                    subtext={kpi.subtext}
                    icon={kpi.icon}
                    goldIcon={kpi.goldIcon}
                  />
                ))}
              </div>
            </section>
          )}

          {/* 6. Professional SVG Chart Components */}
          {(activeSegment === 'all' || activeSegment === 'charts') && (
            <section>
              <div style={{ marginBottom: '12px', fontSize: '13px', fontWeight: 600, color: '#718078', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                6. Professional Chart Card Components (Responsive Native SVG)
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
                {/* Line Chart Card */}
                <AdminCard
                  title="Tenant Growth Trend"
                  subtitle="Client onboarding momentum over 7 months (Design placeholder)"
                  actions={
                    <span style={{ fontSize: '12px', color: '#174D3A', fontWeight: 600 }}>
                      +275% Overall
                    </span>
                  }
                >
                  <AdminLineChart data={demoLineData} unit="clients" />
                </AdminCard>

                {/* Donut Chart Card */}
                <AdminCard
                  title="Product Entitlement Distribution"
                  subtitle="Full Suite vs Single Product Deployments"
                >
                  <AdminDonutChart data={demoDonutData} />
                </AdminCard>
              </div>

              {/* Bar Chart Full Width Card */}
              <div style={{ marginTop: '20px' }}>
                <AdminCard
                  title="Hourly Review System Distribution"
                  subtitle="Local-timezone interaction curve (Design placeholder)"
                >
                  <AdminBarChart data={demoBarData} />
                </AdminCard>
              </div>
            </section>
          )}

          {/* 7. Enterprise Data Table Component */}
          {activeSegment === 'all' && (
            <section>
              <div style={{ marginBottom: '12px', fontSize: '13px', fontWeight: 600, color: '#718078', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                7. Enterprise Data Table Component
              </div>
              <div className="vraja-table-toolbar">
                <div className="vraja-table-toolbar-left">
                  <AdminInput
                    placeholder="Filter clients by name or ID..."
                    value={demoInput}
                    onChange={(e) => setDemoInput(e.target.value)}
                    prefixIcon={
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="11" cy="11" r="8" />
                        <path d="m21 21-4.3-4.3" />
                      </svg>
                    }
                  />
                  <AdminSelect
                    value={demoSelect}
                    onChange={(e) => setDemoSelect(e.target.value)}
                    options={[
                      { value: 'all', label: 'All Statuses' },
                      { value: 'active', label: 'Active Only' },
                      { value: 'suspended', label: 'Suspended Only' },
                    ]}
                  />
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <AdminButton
                    variant="primary"
                    onClick={() => setIsModalOpen(true)}
                  >
                    + Onboard Client
                  </AdminButton>
                </div>
              </div>
              <AdminTable
                columns={demoTableColumns}
                data={demoTableData}
                keyField="id"
                selectable
                selectedKeys={selectedTableKeys}
                onSelectionChange={setSelectedTableKeys}
                pageSize={5}
              />
            </section>
          )}

          {/* 8. Buttons, Inputs, Dropdowns, Badges Showcase */}
          {(activeSegment === 'all' || activeSegment === 'controls') && (
            <section>
              <div style={{ marginBottom: '12px', fontSize: '13px', fontWeight: 600, color: '#718078', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                8 & 9. Buttons, Inputs, Dropdowns, Status Badges & Notifications
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
                {/* Button Palette Card */}
                <AdminCard title="Button Hierarchy" subtitle="Standardized states and variants">
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
                    <AdminButton variant="primary">Deep Emerald (Primary)</AdminButton>
                    <AdminButton variant="secondary">Soft Sage (Secondary)</AdminButton>
                    <AdminButton variant="outline">Subtle Outline</AdminButton>
                    <AdminButton variant="gold">Muted Gold (Accent)</AdminButton>
                    <AdminButton variant="danger">Critical (Danger)</AdminButton>
                    <AdminButton variant="primary" disabled>
                      Disabled State
                    </AdminButton>
                  </div>
                </AdminCard>

                {/* Status Badges Card */}
                <AdminCard title="Semantic Status Badges" subtitle="Operational health indicators">
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
                    <AdminBadge variant="success" dot>Active Service</AdminBadge>
                    <AdminBadge variant="warning" dot>Escalated Issue</AdminBadge>
                    <AdminBadge variant="critical" dot>Suspended Tenant</AdminBadge>
                    <AdminBadge variant="neutral" dot>Offline System</AdminBadge>
                    <AdminBadge variant="gold">Enterprise Tier</AdminBadge>
                  </div>
                  <div style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
                    <EntitlementBadge entitlement="review_manager" />
                    <EntitlementBadge entitlement="digital_card" />
                  </div>
                </AdminCard>
              </div>
            </section>
          )}

          {/* 10. Modals & Confirmation Dialog Trigger Bar */}
          <section>
            <AdminCard
              title="10. Modal & Confirmation Dialog Verification"
              subtitle="Test interactive dialog workflows with live backdrop overlay and keyboard escape support"
            >
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <AdminButton
                  variant="primary"
                  onClick={() => setIsModalOpen(true)}
                >
                  Launch Standard Admin Modal
                </AdminButton>
                <AdminButton
                  variant="danger"
                  onClick={() => setIsConfirmOpen(true)}
                >
                  Launch Critical Confirmation Dialog
                </AdminButton>
              </div>
            </AdminCard>
          </section>
        </main>
      </div>

      {/* 10. Standard Modal Dialog */}
      <AdminModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Enterprise Client Onboarding (Prototype Form)"
        footer={
          <>
            <AdminButton variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </AdminButton>
            <AdminButton
              variant="primary"
              onClick={() => {
                setIsModalOpen(false);
                setActiveNotification({
                  show: true,
                  type: 'success',
                  title: 'Modal Action Confirmed',
                  message: 'Form validation and modal workflow functioning correctly.',
                });
              }}
            >
              Save & Provision
            </AdminButton>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <AdminInput
            label="Business Legal Name"
            placeholder="e.g. Royal Bengal Dining"
            value="Royal Bengal Dining"
            onChange={() => {}}
          />
          <AdminInput
            label="Tenant ID (Slug)"
            placeholder="e.g. royal-bengal"
            value="royal-bengal"
            onChange={() => {}}
            helperText="Indexed unique slug for tenant isolation"
          />
          <AdminSelect
            label="Assigned Package"
            value="both"
            onChange={() => {}}
            options={[
              { value: 'both', label: 'Full Suite (Reviews + Digital Card)' },
              { value: 'review', label: 'Review System Only' },
              { value: 'card', label: 'Digital Card Only' },
            ]}
          />
        </div>
      </AdminModal>

      {/* 10. Confirmation Dialog for Critical Action */}
      <AdminConfirmDialog
        isOpen={isConfirmOpen}
        onClose={() => setIsConfirmOpen(false)}
        onConfirm={() => {
          setIsConfirmOpen(false);
          setActiveNotification({
            show: true,
            type: 'error',
            title: 'Critical Action Executed',
            message: 'Tenant status transition verified in prototype flow.',
          });
        }}
        title="Suspend Tenant Access?"
        description="Are you sure you want to suspend this client? This immediately revokes customer review submissions and public digital card resolution."
        confirmLabel="Yes, Suspend Access"
      />
    </div>
  );
}
