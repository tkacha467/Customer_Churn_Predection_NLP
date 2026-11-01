/**
 * VRAJA AI — Product B Client-Side Security Shield
 * Enterprise client-hardening against unauthorized DevTools inspection,
 * DOM tampering, source viewing, frame hijacking, and console snooping.
 */

export function initSecurityShield() {
  if (typeof window === 'undefined') return () => {};

  // 1. Anti-Clickjacking: Prevent iframe embedding / frame hijacking
  try {
    if (window.top !== window.self) {
      window.top.location = window.self.location;
    }
  } catch {
    // If blocked by cross-origin, hide document body
    if (document.documentElement) {
      document.documentElement.style.display = 'none';
    }
  }

  // 2. Disable Right-Click Context Menu (Prevents "Inspect Element")
  const handleContextMenu = (e) => {
    e.preventDefault();
    return false;
  };

  // 3. Block DevTools & Source Viewing Keyboard Shortcuts
  const handleKeyDown = (e) => {
    // F12 key
    if (e.key === 'F12' || e.keyCode === 123) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }

    const isCtrlOrMeta = e.ctrlKey || e.metaKey;

    // Ctrl/Cmd + Shift + I (Inspect)
    // Ctrl/Cmd + Shift + J (Console)
    // Ctrl/Cmd + Shift + C (Inspect Element)
    if (isCtrlOrMeta && e.shiftKey && (e.key === 'I' || e.key === 'i' || e.key === 'J' || e.key === 'j' || e.key === 'C' || e.key === 'c')) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }

    // Ctrl/Cmd + U (View Page Source)
    if (isCtrlOrMeta && (e.key === 'U' || e.key === 'u')) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }

    // Ctrl/Cmd + S (Save Page)
    if (isCtrlOrMeta && (e.key === 'S' || e.key === 's')) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  };

  // 4. Disable unauthorized asset dragging & image copying
  const handleDragStart = (e) => {
    if (e.target && (e.target.tagName === 'IMG' || e.target.tagName === 'A')) {
      e.preventDefault();
      return false;
    }
  };

  // 5. Silence console probes in production
  if (import.meta.env.PROD) {
    const noop = () => {};
    ['log', 'debug', 'info', 'dir', 'table'].forEach((fn) => {
      try {
        window.console[fn] = noop;
      } catch {
        // preserve environment if frozen
      }
    });

    // 6. Anti-debugger trap (deters DevTools attachment in production)
    const debuggerInterval = setInterval(() => {
      const startTime = performance.now();
      debugger; // eslint-disable-line no-debugger
      if (performance.now() - startTime > 100) {
        // DevTools opened or execution paused by debugger
      }
    }, 2000);

    window.addEventListener('contextmenu', handleContextMenu, { capture: true });
    window.addEventListener('keydown', handleKeyDown, { capture: true });
    window.addEventListener('dragstart', handleDragStart, { capture: true });

    return () => {
      clearInterval(debuggerInterval);
      window.removeEventListener('contextmenu', handleContextMenu, { capture: true });
      window.removeEventListener('keydown', handleKeyDown, { capture: true });
      window.removeEventListener('dragstart', handleDragStart, { capture: true });
    };
  }

  // In development, still block context menu & inspect shortcuts for fidelity
  window.addEventListener('contextmenu', handleContextMenu, { capture: true });
  window.addEventListener('keydown', handleKeyDown, { capture: true });
  window.addEventListener('dragstart', handleDragStart, { capture: true });

  return () => {
    window.removeEventListener('contextmenu', handleContextMenu, { capture: true });
    window.removeEventListener('keydown', handleKeyDown, { capture: true });
    window.removeEventListener('dragstart', handleDragStart, { capture: true });
  };
}

