import React, { Component } from 'react';
import ModelViewer from '@google/model-viewer';

class MiradorModelViewer extends Component {
  render3DViewer() {
    const {
      threeDResources,
      background,
      progressBarHeight,
      progressBarColor,
      autoRotate,
      title,
      annotations = [],  // Assicurarsi che sia sempre un array
    } = this.props;

    console.log("targetProps:", this.props);  // Debug per verificare targetProps e le annotazioni

    const styles = {
      width: "100%",
      height: "100%",
      background,
    };

    const progressBarStyle = {
      "--progress-bar-height": progressBarHeight,
      "--progress-bar-color": progressBarColor,
    };

    return (
      <model-viewer
        style={{ ...styles, ...progressBarStyle }}
        src={threeDResources[0].id}
        alt={title}
        auto-rotate={autoRotate ? true : undefined}
        camera-controls
      >
        {/* Genera dinamicamente le annotazioni */}
        {annotations.map((annotation, index) => (
          <div
            key={index}
            slot={`hotspot-${index + 1}`}
            data-position={`${annotation.x * 0.5} ${annotation.y * 0.5} ${annotation.z * 0.5}`}  // Applica un fattore di scala
            data-normal="0 1 0"
            style={{
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              color: 'white',
              padding: '5px',
              borderRadius: '5px',
            }}
          >
            {annotation.text}
          </div>
        ))}
      </model-viewer>
    );
  }

  render() {
    const { TargetComponent, targetProps, threeDResources } = this.props;
    return threeDResources && threeDResources.length > 0
      ? this.render3DViewer()
      : <TargetComponent {...targetProps} />;
  }
}

export default MiradorModelViewer;
