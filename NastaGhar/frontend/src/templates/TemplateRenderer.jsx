import React, { Component } from 'react';
import { resolveTemplateComponent } from './registry';
import FallbackTemplate from './FallbackTemplate';
import './templates.css';

class TemplateErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Template rendering error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <FallbackTemplate
          templateData={this.props.templateData}
          journeyState={this.props.journeyState}
        />
      );
    }
    return this.props.children;
  }
}

/**
 * TemplateRenderer
 * Normalizes template configuration and mounts the exact visual skin
 * passing the complete 7-stage review journey state and callbacks.
 */
export default function TemplateRenderer({ templateData, journeyState }) {
  const ResolvedComponent = resolveTemplateComponent(templateData);

  return (
    <TemplateErrorBoundary templateData={templateData} journeyState={journeyState}>
      <div className="vt-renderer-wrapper" data-template-slug={templateData?.template?.slug || 'default'}>
        <ResolvedComponent templateData={templateData} journeyState={journeyState} />
      </div>
    </TemplateErrorBoundary>
  );
}
