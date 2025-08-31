import React, { useState, useCallback } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import { Box, Paper, Typography, IconButton, Tooltip } from '@mui/material';
import { 
  DragIndicator, 
  Fullscreen, 
  FullscreenExit, 
  Close,
  Settings 
} from '@mui/icons-material';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

const DashboardGrid = ({ 
  layout, 
  components, 
  cols = 12, 
  rowHeight = 60,
  onLayoutChange 
}) => {
  const [layouts, setLayouts] = useState({ lg: layout });
  const [fullscreenComponent, setFullscreenComponent] = useState(null);
  const [hiddenComponents, setHiddenComponents] = useState(new Set());

  const handleLayoutChange = useCallback((layout, layouts) => {
    setLayouts(layouts);
    if (onLayoutChange) {
      onLayoutChange(layout, layouts);
    }
  }, [onLayoutChange]);

  const handleFullscreen = (componentId) => {
    setFullscreenComponent(componentId);
  };

  const handleExitFullscreen = () => {
    setFullscreenComponent(null);
  };

  const handleHideComponent = (componentId) => {
    setHiddenComponents(prev => new Set([...prev, componentId]));
  };

  const handleShowComponent = (componentId) => {
    setHiddenComponents(prev => {
      const newSet = new Set(prev);
      newSet.delete(componentId);
      return newSet;
    });
  };

  const GridItem = ({ componentId, children }) => {
    const isHidden = hiddenComponents.has(componentId);
    const isFullscreen = fullscreenComponent === componentId;

    if (isHidden && !isFullscreen) {
      return null;
    }

    return (
      <Paper
        elevation={2}
        sx={{
          height: '100%',
          overflow: 'hidden',
          position: 'relative',
          borderRadius: 2,
          '&:hover .grid-item-controls': {
            opacity: 1
          }
        }}
      >
        {/* Grid Item Controls */}
        <Box
          className="grid-item-controls"
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            display: 'flex',
            gap: 0.5,
            opacity: 0,
            transition: 'opacity 0.2s ease',
            zIndex: 1000,
            bgcolor: 'background.paper',
            borderRadius: 1,
            p: 0.5,
            boxShadow: 1
          }}
        >
          <Tooltip title="Drag to move">
            <IconButton 
              size="small" 
              className="drag-handle"
              sx={{ cursor: 'move' }}
            >
              <DragIndicator fontSize="small" />
            </IconButton>
          </Tooltip>
          
          <Tooltip title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}>
            <IconButton 
              size="small"
              onClick={() => isFullscreen ? handleExitFullscreen() : handleFullscreen(componentId)}
            >
              {isFullscreen ? 
                <FullscreenExit fontSize="small" /> : 
                <Fullscreen fontSize="small" />
              }
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Hide panel">
            <IconButton 
              size="small"
              onClick={() => handleHideComponent(componentId)}
            >
              <Close fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Component Content */}
        <Box 
          sx={{ 
            height: '100%',
            overflow: 'hidden',
            '& .MuiCard-root': {
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              '& .MuiCardContent-root': {
                flex: 1,
                overflow: 'auto',
                '&:last-child': {
                  paddingBottom: '16px'
                }
              }
            }
          }}
        >
          {children}
        </Box>
      </Paper>
    );
  };

  // Fullscreen modal
  if (fullscreenComponent) {
    return (
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          bgcolor: 'background.default',
          zIndex: 2000,
          p: 2
        }}
      >
        <Box
          sx={{
            height: '100%',
            position: 'relative'
          }}
        >
          <IconButton
            sx={{
              position: 'absolute',
              top: 16,
              right: 16,
              zIndex: 1,
              bgcolor: 'background.paper',
              boxShadow: 2
            }}
            onClick={handleExitFullscreen}
          >
            <FullscreenExit />
          </IconButton>
          {components[fullscreenComponent]}
        </Box>
      </Box>
    );
  }

  // Filter out hidden components from layout
  const visibleLayout = layouts.lg?.filter(item => !hiddenComponents.has(item.i)) || [];

  return (
    <Box sx={{ height: '100%', overflow: 'hidden' }}>
      {/* Hidden Components Bar */}
      {hiddenComponents.size > 0 && (
        <Box 
          sx={{ 
            mb: 2, 
            p: 1, 
            bgcolor: 'action.hover', 
            borderRadius: 1,
            display: 'flex',
            gap: 1,
            alignItems: 'center',
            flexWrap: 'wrap'
          }}
        >
          <Typography variant="caption" color="textSecondary" sx={{ mr: 1 }}>
            Hidden panels:
          </Typography>
          {Array.from(hiddenComponents).map(componentId => (
            <Box
              key={componentId}
              onClick={() => handleShowComponent(componentId)}
              sx={{
                px: 1,
                py: 0.5,
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
                borderRadius: 1,
                cursor: 'pointer',
                fontSize: '0.75rem',
                '&:hover': {
                  bgcolor: 'primary.dark'
                }
              }}
            >
              {componentId.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </Box>
          ))}
        </Box>
      )}

      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        onLayoutChange={handleLayoutChange}
        cols={{ lg: cols, md: 8, sm: 4, xs: 2, xxs: 1 }}
        rowHeight={rowHeight}
        draggableHandle=".drag-handle"
        compactType="vertical"
        preventCollision={false}
        margin={[16, 16]}
        containerPadding={[0, 0]}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        style={{ minHeight: '100%' }}
      >
        {visibleLayout.map(item => (
          <div key={item.i}>
            <GridItem componentId={item.i}>
              {components[item.i]}
            </GridItem>
          </div>
        ))}
      </ResponsiveGridLayout>

      <style jsx global>{`
        .react-grid-item {
          transition: transform 200ms ease, width 200ms ease, height 200ms ease;
        }
        
        .react-grid-item.react-grid-placeholder {
          background: rgba(25, 118, 210, 0.15) !important;
          border: 2px dashed rgba(25, 118, 210, 0.4) !important;
          border-radius: 8px;
          opacity: 0.8;
          transition: all 200ms ease;
        }

        .react-grid-item > .react-resizable-handle {
          background-color: transparent;
          background-image: none;
        }

        .react-grid-item > .react-resizable-handle::after {
          content: '';
          position: absolute;
          right: 0;
          bottom: 0;
          width: 16px;
          height: 16px;
          background: linear-gradient(
            -45deg,
            transparent 0px,
            transparent 4px,
            rgba(0, 0, 0, 0.3) 4px,
            rgba(0, 0, 0, 0.3) 5px,
            transparent 5px,
            transparent 8px,
            rgba(0, 0, 0, 0.3) 8px,
            rgba(0, 0, 0, 0.3) 9px,
            transparent 9px,
            transparent 12px,
            rgba(0, 0, 0, 0.3) 12px,
            rgba(0, 0, 0, 0.3) 13px,
            transparent 13px
          );
          transform: rotate(45deg);
          border-radius: 0 0 4px 0;
        }

        .react-grid-item.react-grid-item--static > .react-resizable-handle {
          display: none;
        }

        .react-grid-item.cssTransforms {
          transition-property: transform, width, height;
        }

        .react-grid-item.resizing {
          opacity: 0.9;
          z-index: 1000;
        }

        .react-grid-item.react-draggable-dragging {
          transition: none;
          z-index: 1000;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .react-grid-layout {
          position: relative;
          min-height: 100%;
        }
        
        .grid-item-controls {
          backdrop-filter: blur(10px);
        }

        /* Dark mode adjustments */
        @media (prefers-color-scheme: dark) {
          .react-grid-item > .react-resizable-handle::after {
            background: linear-gradient(
              -45deg,
              transparent 0px,
              transparent 4px,
              rgba(255, 255, 255, 0.3) 4px,
              rgba(255, 255, 255, 0.3) 5px,
              transparent 5px,
              transparent 8px,
              rgba(255, 255, 255, 0.3) 8px,
              rgba(255, 255, 255, 0.3) 9px,
              transparent 9px,
              transparent 12px,
              rgba(255, 255, 255, 0.3) 12px,
              rgba(255, 255, 255, 0.3) 13px,
              transparent 13px
            );
          }
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
          .grid-item-controls {
            opacity: 1;
          }
        }
      `}</style>
    </Box>
  );
};

export default DashboardGrid;