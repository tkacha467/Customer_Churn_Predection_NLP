import { useState } from 'react';

/**
 * Responsive Enterprise Line / Area Trend Chart
 */
export function AdminLineChart({
  data = [], // [{ label: 'Mon', value: 45 }]
  height = 200,
  strokeColor = '#174D3A',
  fillGradient = true,
  unit = '',
}) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  if (!data || data.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#718078' }}>
        No chart data available
      </div>
    );
  }

  const values = data.map((d) => d.value);
  const minVal = 0;
  const maxVal = Math.max(...values, 10);
  const paddingX = 40;
  const paddingY = 25;
  const width = 600;

  const getX = (index) => paddingX + (index / (data.length - 1)) * (width - paddingX * 2);
  const getY = (val) => height - paddingY - ((val - minVal) / (maxVal - minVal)) * (height - paddingY * 2);

  const points = data.map((d, i) => `${getX(i)},${getY(d.value)}`).join(' ');
  const areaPath = `${points} L ${getX(data.length - 1)},${height - paddingY} L ${getX(0)},${height - paddingY} Z`;

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}
      >
        <defs>
          <linearGradient id="emeraldAreaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#174D3A" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#174D3A" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Horizontal grid lines */}
        {[0, 0.33, 0.66, 1].map((ratio, i) => {
          const y = height - paddingY - ratio * (height - paddingY * 2);
          const gridVal = Math.round(minVal + ratio * (maxVal - minVal));
          return (
            <g key={i}>
              <line
                x1={paddingX}
                y1={y}
                x2={width - paddingX}
                y2={y}
                stroke="#E3E8E3"
                strokeDasharray="4 4"
              />
              <text
                x={paddingX - 10}
                y={y + 4}
                textAnchor="end"
                fontSize="11"
                fill="#718078"
                fontFamily="sans-serif"
              >
                {gridVal}
              </text>
            </g>
          );
        })}

        {/* Filled Area */}
        {fillGradient && <path d={`M ${areaPath}`} fill="url(#emeraldAreaGrad)" />}

        {/* Line Stroke */}
        <polyline
          fill="none"
          stroke={strokeColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />

        {/* Interactive Points */}
        {data.map((d, i) => {
          const cx = getX(i);
          const cy = getY(d.value);
          const isHovered = hoveredIndex === i;

          return (
            <g
              key={i}
              onMouseEnter={() => setHoveredIndex(i)}
              onMouseLeave={() => setHoveredIndex(null)}
              style={{ cursor: 'pointer' }}
            >
              <circle
                cx={cx}
                cy={cy}
                r={isHovered ? 6 : 4}
                fill={isHovered ? '#C6A66B' : strokeColor}
                stroke="#FFFFFF"
                strokeWidth={isHovered ? 3 : 2}
                transition="all 0.15s ease"
              />
              {/* X Axis Labels */}
              <text
                x={cx}
                y={height - 6}
                textAnchor="middle"
                fontSize="11"
                fill="#718078"
                fontFamily="sans-serif"
              >
                {d.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Floating Tooltip */}
      {hoveredIndex !== null && (
        <div
          style={{
            position: 'absolute',
            top: '8px',
            right: '12px',
            backgroundColor: '#26352D',
            color: '#FFFFFF',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            pointerEvents: 'none',
          }}
        >
          <span style={{ color: '#DCE5DD' }}>{data[hoveredIndex].label}: </span>
          <strong>{data[hoveredIndex].value} {unit}</strong>
        </div>
      )}
    </div>
  );
}

/**
 * Responsive Enterprise Bar Chart
 */
export function AdminBarChart({
  data = [], // [{ label: '12:00', value: 80 }]
  height = 180,
  barColor = '#174D3A',
}) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  if (!data || data.length === 0) return null;

  const maxVal = Math.max(...data.map((d) => d.value), 10);
  const width = 600;
  const paddingX = 30;
  const paddingY = 25;
  const chartWidth = width - paddingX * 2;
  const slotWidth = chartWidth / data.length;
  const barWidth = Math.min(Math.max(slotWidth * 0.55, 12), 36);

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}
      >
        {/* Baseline */}
        <line
          x1={paddingX}
          y1={height - paddingY}
          x2={width - paddingX}
          y2={height - paddingY}
          stroke="#E3E8E3"
          strokeWidth="1.5"
        />

        {data.map((d, i) => {
          const barHeight = ((d.value / maxVal) * (height - paddingY * 2));
          const x = paddingX + i * slotWidth + (slotWidth - barWidth) / 2;
          const y = height - paddingY - barHeight;
          const isHovered = hoveredIndex === i;

          return (
            <g
              key={i}
              onMouseEnter={() => setHoveredIndex(i)}
              onMouseLeave={() => setHoveredIndex(null)}
              style={{ cursor: 'pointer' }}
            >
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={Math.max(barHeight, 2)}
                rx="4"
                ry="4"
                fill={isHovered ? '#C6A66B' : barColor}
                opacity={isHovered ? 1 : 0.88}
              />
              <text
                x={x + barWidth / 2}
                y={height - 8}
                textAnchor="middle"
                fontSize="11"
                fill="#718078"
                fontFamily="sans-serif"
              >
                {d.label}
              </text>
            </g>
          );
        })}
      </svg>

      {hoveredIndex !== null && (
        <div
          style={{
            position: 'absolute',
            top: '4px',
            right: '12px',
            backgroundColor: '#26352D',
            color: '#FFFFFF',
            padding: '4px 10px',
            borderRadius: '6px',
            fontSize: '12px',
          }}
        >
          <span>{data[hoveredIndex].label}: </span>
          <strong>{data[hoveredIndex].value}</strong>
        </div>
      )}
    </div>
  );
}

/**
 * Enterprise Donut Distribution Chart
 */
export function AdminDonutChart({
  data = [], // [{ label: 'Full Suite', count: 18, color: '#174D3A' }]
  size = 180,
  strokeWidth = 26,
}) {
  const total = data.reduce((sum, item) => sum + (item.count || 0), 0) || 1;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  let accumulatedPercent = 0;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
      <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background circle track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="#E3E8E3"
            strokeWidth={strokeWidth}
          />
          {data.map((item, index) => {
            const percent = (item.count / total) * 100;
            const strokeDasharray = `${(percent / 100) * circumference} ${circumference}`;
            const strokeDashoffset = -((accumulatedPercent / 100) * circumference);
            accumulatedPercent += percent;

            return (
              <circle
                key={index}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="transparent"
                stroke={item.color || '#174D3A'}
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                transform={`rotate(-90 ${size / 2} ${size / 2})`}
                style={{ transition: 'stroke-dasharray 0.3s ease' }}
              />
            );
          })}
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
          }}
        >
          <span style={{ fontSize: '24px', fontWeight: 700, color: '#26352D', lineHeight: 1 }}>
            {total}
          </span>
          <span style={{ fontSize: '11px', color: '#718078', textTransform: 'uppercase', marginTop: '4px' }}>
            Total
          </span>
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {data.map((item, idx) => {
          const pct = Math.round((item.count / total) * 100);
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
              <span
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '3px',
                  backgroundColor: item.color || '#174D3A',
                  display: 'inline-block',
                }}
              />
              <span style={{ color: '#26352D', fontWeight: 500 }}>{item.label}</span>
              <span style={{ color: '#718078', marginLeft: 'auto', fontVariantNumeric: 'tabular-nums' }}>
                {item.count} ({pct}%)
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
