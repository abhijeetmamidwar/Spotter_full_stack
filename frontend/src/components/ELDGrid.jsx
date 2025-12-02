import React from 'react';

const ELDGrid = ({ events, date }) => {
  // Dimensions
  const width = 800;
  const height = 200;
  const margin = { top: 20, right: 30, bottom: 30, left: 100 };
  const graphWidth = width - margin.left - margin.right;
  const graphHeight = height - margin.top - margin.bottom;

  // Y-axis positions for the 4 statuses
  const statusY = {
    "OFF_DUTY": 0,
    "SLEEPER": graphHeight / 3,
    "DRIVING": (graphHeight / 3) * 2,
    "ON_DUTY": graphHeight
  };

  // Helper to get X coordinate from time string (ISO)
  const getX = (isoString) => {
    const dateObj = new Date(isoString);
    // We calculate seconds relative to the start of this specific day
    // This handles the case where an event ends at 00:00 of the NEXT day (24:00)
    // correctly mapping it to the end of the graph instead of the beginning.
    const dayStart = new Date(date + "T00:00:00");
    
    // Calculate difference in seconds
    let diffSeconds = (dateObj - dayStart) / 1000;
    
    // Clamp to 0-86400 to be safe (though backend should be precise)
    diffSeconds = Math.max(0, Math.min(86400, diffSeconds));
    
    return (diffSeconds / 86400) * graphWidth;
  };

  // Generate path data
  let pathD = "";
  if (events && events.length > 0) {
    // Sort events by time just in case
    const sortedEvents = [...events].sort((a, b) => new Date(a.start) - new Date(b.start));
    
    // Start point
    const first = sortedEvents[0];
    let currentX = getX(first.start);
    let currentY = statusY[first.status];
    
    pathD += `M ${currentX} ${currentY}`;
    
    sortedEvents.forEach(event => {
      const startX = getX(event.start);
      const endX = getX(event.end);
      const y = statusY[event.status];
      
      // Vertical line to new status (if changed)
      if (y !== currentY) {
        pathD += ` L ${startX} ${y}`;
      }
      
      // Horizontal line for duration
      pathD += ` L ${endX} ${y}`;
      
      currentX = endX;
      currentY = y;
    });
  }

  return (
    <div className="border rounded p-4 bg-white shadow-sm mb-4">
      <h3 className="font-bold text-lg mb-2">Date: {date}</h3>
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
        <g transform={`translate(${margin.left}, ${margin.top})`}>
          {/* Grid Lines & Labels */}
          {[0, 1, 2, 3].map(i => (
            <g key={i}>
              <line 
                x1={0} y1={i * (graphHeight / 3)} 
                x2={graphWidth} y2={i * (graphHeight / 3)} 
                stroke="#e5e7eb" strokeWidth="1" 
              />
              <text 
                x={-10} y={i * (graphHeight / 3)} 
                dy="0.32em" textAnchor="end" className="text-xs font-semibold fill-gray-600"
              >
                {Object.keys(statusY).find(key => statusY[key] === i * (graphHeight / 3)).replace('_', ' ')}
              </text>
            </g>
          ))}
          
          {/* Hour Markers */}
          {[...Array(25)].map((_, i) => (
            <g key={i}>
              <line 
                x1={(i / 24) * graphWidth} y1={0} 
                x2={(i / 24) * graphWidth} y2={graphHeight} 
                stroke="#e5e7eb" strokeWidth="1" 
              />
              <text 
                x={(i / 24) * graphWidth} y={graphHeight + 20} 
                textAnchor="middle" className="text-xs fill-gray-500"
              >
                {i}
              </text>
            </g>
          ))}

          {/* The Data Path */}
          <path d={pathD} fill="none" stroke="#2563eb" strokeWidth="2" />
        </g>
      </svg>
    </div>
  );
};

export default ELDGrid;
