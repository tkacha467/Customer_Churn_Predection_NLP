import { useState } from 'react';

/**
 * Enterprise Data Table Component
 */
export function AdminTable({
  columns = [], // [{ key: 'id', title: 'Tenant', sortable: true, render: (row) => ... }]
  data = [],
  keyField = 'id',
  selectable = false,
  selectedKeys = [],
  onSelectionChange,
  emptyMessage = 'No records found',
  pageSize = 10,
}) {
  const [sortKey, setSortKey] = useState(null);
  const [sortOrder, setSortOrder] = useState('asc'); // asc | desc
  const [currentPage, setCurrentPage] = useState(1);

  // Sorting
  const handleSort = (colKey) => {
    if (sortKey === colKey) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(colKey);
      setSortOrder('asc');
    }
  };

  const sortedData = [...data].sort((a, b) => {
    if (!sortKey) return 0;
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    if (aVal === bVal) return 0;
    if (aVal === null || aVal === undefined) return 1;
    if (bVal === null || bVal === undefined) return -1;
    if (typeof aVal === 'string') {
      return sortOrder === 'asc'
        ? aVal.localeCompare(String(bVal))
        : String(bVal).localeCompare(aVal);
    }
    return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
  });

  // Pagination
  const totalPages = Math.ceil(sortedData.length / pageSize) || 1;
  const paginatedData = sortedData.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  // Selection
  const allSelected =
    paginatedData.length > 0 &&
    paginatedData.every((row) => selectedKeys.includes(row[keyField]));

  const handleSelectAll = () => {
    if (!onSelectionChange) return;
    if (allSelected) {
      const pageKeys = new Set(paginatedData.map((r) => r[keyField]));
      onSelectionChange(selectedKeys.filter((k) => !pageKeys.has(k)));
    } else {
      const newKeys = new Set([...selectedKeys, ...paginatedData.map((r) => r[keyField])]);
      onSelectionChange(Array.from(newKeys));
    }
  };

  const handleSelectRow = (key) => {
    if (!onSelectionChange) return;
    if (selectedKeys.includes(key)) {
      onSelectionChange(selectedKeys.filter((k) => k !== key));
    } else {
      onSelectionChange([...selectedKeys, key]);
    }
  };

  return (
    <div className="vraja-table-container">
      <table className="vraja-table">
        <thead>
          <tr>
            {selectable && (
              <th style={{ width: '40px', textAlign: 'center' }}>
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={handleSelectAll}
                  style={{ cursor: 'pointer', accentColor: '#174D3A' }}
                  aria-label="Select all rows"
                />
              </th>
            )}
            {columns.map((col) => (
              <th
                key={col.key}
                className={col.sortable ? 'sortable' : ''}
                onClick={col.sortable ? () => handleSort(col.key) : undefined}
                style={{ textAlign: col.align || 'left', width: col.width }}
              >
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  <span>{col.title}</span>
                  {col.sortable && sortKey === col.key && (
                    <span style={{ fontSize: '10px' }}>
                      {sortOrder === 'asc' ? '▲' : '▼'}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {paginatedData.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length + (selectable ? 1 : 0)}
                style={{ textAlign: 'center', padding: '36px', color: '#718078' }}
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            paginatedData.map((row) => {
              const rowKey = row[keyField];
              const isSelected = selectedKeys.includes(rowKey);

              return (
                <tr
                  key={rowKey}
                  style={isSelected ? { backgroundColor: '#F5F8F6' } : undefined}
                >
                  {selectable && (
                    <td style={{ textAlign: 'center' }}>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleSelectRow(rowKey)}
                        style={{ cursor: 'pointer', accentColor: '#174D3A' }}
                        aria-label={`Select row ${rowKey}`}
                      />
                    </td>
                  )}
                  {columns.map((col) => (
                    <td key={col.key} style={{ textAlign: col.align || 'left' }}>
                      {col.render ? col.render(row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              );
            })
          )}
        </tbody>
      </table>

      {/* Pagination Bar */}
      <div className="vraja-table-pagination">
        <div>
          Showing{' '}
          <strong style={{ color: '#26352D' }}>
            {data.length === 0 ? 0 : (currentPage - 1) * pageSize + 1}
          </strong>{' '}
          to{' '}
          <strong style={{ color: '#26352D' }}>
            {Math.min(currentPage * pageSize, data.length)}
          </strong>{' '}
          of <strong style={{ color: '#26352D' }}>{data.length}</strong> records
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            type="button"
            className="vraja-btn vraja-btn-outline vraja-btn-sm"
            disabled={currentPage <= 1}
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </button>
          <span style={{ padding: '0 8px', fontSize: '12px' }}>
            Page {currentPage} of {totalPages}
          </span>
          <button
            type="button"
            className="vraja-btn vraja-btn-outline vraja-btn-sm"
            disabled={currentPage >= totalPages}
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

export default AdminTable;
