import React from "react";

function EngagementChart() {
  const data = [
    { day: "Mon", reach: 42, engagement: 28 },
    { day: "Tue", reach: 58, engagement: 40 },
    { day: "Wed", reach: 48, engagement: 34 },
    { day: "Thu", reach: 72, engagement: 52 },
    { day: "Fri", reach: 64, engagement: 47 },
    { day: "Sat", reach: 86, engagement: 68 },
    { day: "Sun", reach: 78, engagement: 61 },
  ];

  const width = 760;
  const height = 260;
  const paddingX = 20;
  const paddingY = 25;

  const getPoints = (key) =>
    data.map((item, index) => ({
      x:
        paddingX +
        (index * (width - paddingX * 2)) /
          (data.length - 1),

      y:
        height -
        paddingY -
        (item[key] / 100) *
          (height - paddingY * 2),

      value: item[key],
      day: item.day,
    }));

  const reachPoints = getPoints("reach");
  const engagementPoints = getPoints("engagement");

  const makeLine = (points) =>
    points.map((point) => `${point.x},${point.y}`).join(" ");

  const makeArea = (points) =>
    [
      `${points[0].x},${height - paddingY}`,
      ...points.map((point) => `${point.x},${point.y}`),
      `${points[points.length - 1].x},${height - paddingY}`,
    ].join(" ");

  return (
    <div className="engagement-chart-card">

      {/* Header */}
      <div className="chart-header">

        <div>
          <h3>Engagement Overview</h3>
          <p>Your social media performance this week</p>
        </div>

        <select className="chart-select">
          <option>Last 7 days</option>
          <option>Last 30 days</option>
          <option>Last 3 months</option>
        </select>

      </div>

      {/* Legend */}
      <div className="chart-legend">

        <div className="legend-item">
          <span className="legend-dot reach-dot"></span>
          Reach
        </div>

        <div className="legend-item">
          <span className="legend-dot engagement-dot"></span>
          Engagement
        </div>

      </div>

      {/* Chart */}
      <div className="line-chart-container">

        <div className="chart-y-labels">
          <span>100</span>
          <span>75</span>
          <span>50</span>
          <span>25</span>
          <span>0</span>
        </div>

        <svg
          className="line-chart"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
        >

          <defs>

            {/* Reach gradient */}
            <linearGradient
              id="reachGradient"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="0%"
                stopColor="#22d3ee"
                stopOpacity="0.25"
              />

              <stop
                offset="100%"
                stopColor="#22d3ee"
                stopOpacity="0"
              />
            </linearGradient>

            {/* Engagement gradient */}
            <linearGradient
              id="engagementGradient"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="0%"
                stopColor="#a855f7"
                stopOpacity="0.22"
              />

              <stop
                offset="100%"
                stopColor="#a855f7"
                stopOpacity="0"
              />
            </linearGradient>

          </defs>

          {/* Grid */}
          {[0, 25, 50, 75, 100].map((value) => {

            const y =
              height -
              paddingY -
              (value / 100) *
                (height - paddingY * 2);

            return (
              <line
                key={value}
                x1="0"
                y1={y}
                x2={width}
                y2={y}
                className="chart-grid-line"
              />
            );
          })}

          {/* Reach area */}
          <polygon
            points={makeArea(reachPoints)}
            fill="url(#reachGradient)"
          />

          {/* Engagement area */}
          <polygon
            points={makeArea(engagementPoints)}
            fill="url(#engagementGradient)"
          />

          {/* Reach glow */}
          <polyline
            points={makeLine(reachPoints)}
            fill="none"
            stroke="#22d3ee"
            strokeWidth="8"
            opacity="0.18"
            filter="blur(5px)"
          />

          {/* Reach line */}
          <polyline
            points={makeLine(reachPoints)}
            fill="none"
            stroke="#22d3ee"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="reach-line"
          />

          {/* Engagement glow */}
          <polyline
            points={makeLine(engagementPoints)}
            fill="none"
            stroke="#a855f7"
            strokeWidth="8"
            opacity="0.18"
            filter="blur(5px)"
          />

          {/* Engagement line */}
          <polyline
            points={makeLine(engagementPoints)}
            fill="none"
            stroke="#a855f7"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="engagement-line"
          />

          {/* Reach points */}
          {reachPoints.map((point) => (
            <g key={`reach-${point.day}`}>
              <circle
                cx={point.x}
                cy={point.y}
                r="8"
                fill="#22d3ee"
                opacity="0.18"
              />

              <circle
                cx={point.x}
                cy={point.y}
                r="4"
                fill="#67e8f9"
                stroke="#171923"
                strokeWidth="2"
                className="chart-point"
              />
            </g>
          ))}

          {/* Engagement points */}
          {engagementPoints.map((point) => (
            <g key={`engagement-${point.day}`}>
              <circle
                cx={point.x}
                cy={point.y}
                r="8"
                fill="#a855f7"
                opacity="0.18"
              />

              <circle
                cx={point.x}
                cy={point.y}
                r="4"
                fill="#c084fc"
                stroke="#171923"
                strokeWidth="2"
                className="chart-point"
              />
            </g>
          ))}

        </svg>

        {/* X labels */}
        <div className="chart-x-labels">
          {data.map((item) => (
            <span key={item.day}>{item.day}</span>
          ))}
        </div>

      </div>

    </div>
  );
}

export default EngagementChart;