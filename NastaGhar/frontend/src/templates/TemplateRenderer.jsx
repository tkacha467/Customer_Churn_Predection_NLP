import React from 'react';
import { resolveTemplateComponent } from './registry';

/**
 * TemplateRenderer
 * Normalizes template configuration and mounts the exact visual skin
 * passing the complete 7-stage review journey state and callbacks.
 */
export default function TemplateRenderer({ templateData, journeyState }) {
  const Component = resolveTemplateComponent(templateData);

  return (
    <div className="vt-renderer-wrapper" data-template-slug={templateData?.template?.slug || 'default'}>
      <Component templateData={templateData} journeyState={journeyState} />
    </div>
  );
}
