import React, { Component } from 'react';
import ModelViewer from '@google/model-viewer';
import {
  getCurrentCanvas, getManifestTitle, getWindowConfig
} from 'mirador/dist/es/src/state/selectors';
import flattenDeep from 'lodash/flattenDeep';
import flatten from 'lodash/flatten';

import MiradorModelViewer from './MiradorModelViewer';

// Funzione per ottenere le risorse 3D dal canvas
function threeDResources(canvas) {
  if (canvas != undefined) {
    const resources = flattenDeep([
      canvas.getContent().map(i => i.getBody()),
    ]);
    return flatten(resources.filter((resource) => resource.getProperty('type') === 'Model'));
  } else {
    return [];
  }
}

// Funzione per ottenere le annotazioni dal canvas corrente
function extractAnnotations(canvas) {
  if (!canvas || !canvas.__jsonld.annotations) return [];

  // Estrai le annotazioni 3D con coordinate e testo
  const annotations = [];
  canvas.__jsonld.annotations.forEach(annotationPage => {
    annotationPage.items.forEach(annotation => {
      const selector = annotation.target.selector;
      if (selector && selector.type === 'FragmentSelector' && selector.value.startsWith('xyz=')) {
        const [x, y, z] = selector.value.replace('xyz=', '').split(',').map(Number);
        annotations.push({
          x,
          y,
          z,
          text: annotation.body.value || "",
        });
      }
    });
  });

  return annotations;
}

// Aggiorna mapStateToProps per passare anche le annotazioni come prop
const mapStateToProps = (state, { canvasId, windowId }) => {
  const canvas = getCurrentCanvas(state, { canvasId, windowId });
  return {
    threeDResources: threeDResources(canvas),
    annotations: extractAnnotations(canvas),  // Aggiungi le annotazioni estratte
    title: getManifestTitle(state, { canvasId, windowId }),
    background: getWindowConfig(state, { windowId }).modelViewerBackground || "#000000",
    progressBarHeight: getWindowConfig(state, { windowId }).modelViewerProgressHeight || "5px",
    progressBarColor: getWindowConfig(state, { windowId }).modelViewerProgressColor || "rgba(0, 0, 0, 0.4)",
    autoRotate: getWindowConfig(state, { windowId }).modelViewerAutoRotate || false,
  };
};

export default {
  target: 'WindowViewer',
  mode: 'wrap',
  component: MiradorModelViewer,
  mapStateToProps: mapStateToProps
};
