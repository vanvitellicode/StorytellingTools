// Viewer.js completo per aggiungere annotazioni al modello 3D con il mouse

// Imposta Three.js con scena, camera e renderer
const viewer = document.getElementById('viewer');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, viewer.clientWidth / viewer.clientHeight, 0.1, 1000);
camera.position.z = 5;

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(viewer.clientWidth, viewer.clientHeight);
viewer.appendChild(renderer.domElement);

// Aggiungi luce alla scena
const ambientLight = new THREE.AmbientLight(0xffffff, 1);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
directionalLight.position.set(10, 10, 10).normalize();
scene.add(directionalLight);

// Aggiungi controlli OrbitControls
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.screenSpacePanning = false;
controls.maxPolarAngle = Math.PI / 2;

// Variabile per il modello caricato
let model;
const annotations = []; // Array per memorizzare le annotazioni

// Gestisci il caricamento del file GLB dall'utente
const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file) {
        const url = URL.createObjectURL(file);

        // Calcola il checksum
        const arrayBuffer = await file.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const checksum = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

        // Salva il checksum come attributo personalizzato dell'input file
        fileInput.dataset.checksum = checksum;

        // Carica il modello con il checksum
        loadModel(url, checksum);
    }
});


async function deleteAnnotation(annotation) {
    try {
        const response = await fetch('/src/delete_annotation.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                x: annotation.position.x,
                y: annotation.position.y,
                z: annotation.position.z,
                text: annotation.text
            }),
        });

        if (!response.ok) {
            throw new Error('Errore durante l\'eliminazione dell\'annotazione');
        }

        // Rimuovi la sfera e l'etichetta dalla scena e dal DOM
        scene.remove(annotation.marker);
        document.body.removeChild(annotation.label);

        // Rimuovi l'annotazione dall'array
        const index = annotations.indexOf(annotation);
        if (index > -1) {
            annotations.splice(index, 1);
        }

        // Rimuovi la riga dalla tabella HTML
        const annotationsTableBody = document.querySelector('#annotationsTable tbody');
        const rows = annotationsTableBody.querySelectorAll('tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 4) {
                const x = parseFloat(cells[0].innerText);
                const y = parseFloat(cells[1].innerText);
                const z = parseFloat(cells[2].innerText);
                const text = cells[3].innerText;

                if (x === annotation.position.x && y === annotation.position.y && z === annotation.position.z && text === annotation.text) {
                    annotationsTableBody.removeChild(row);
                }
            }
        });

    } catch (error) {
        console.error('Errore durante l\'eliminazione dell\'annotazione:', error);
    }
}

// Aggiorna il caricamento delle annotazioni nella tabella
function loadModel(url, checksum) {
    const loader = new THREE.GLTFLoader();
    loader.load(url, (gltf) => {
        model = gltf.scene;
        model.scale.set(2, 2, 2);
        model.position.set(0, 0, 0);

        // Aggiungi il modello alla scena principale
        scene.add(model);
        const annotationsTableBody = document.querySelector('#annotationsTable tbody');
        annotationsTableBody.innerHTML = ''; // Pulisce la tabella

        // Recupera annotazioni salvate se disponibili
        fetchAnnotationsFromDatabase(checksum).then(savedAnnotations => {
            savedAnnotations.forEach(annotationData => {
                const markerGeometry = new THREE.TorusGeometry(0.05, 0.02, 16, 100);
                const markerMaterial = new THREE.MeshStandardMaterial({ color: 0xff0000, metalness: 0.6, roughness: 0.2 });
                const marker = new THREE.Mesh(markerGeometry, markerMaterial);
                marker.position.set(annotationData.position.x, annotationData.position.y, annotationData.position.z);
                scene.add(marker);

                const annotationLabel = document.createElement('div');
                annotationLabel.className = 'annotation-label';
                annotationLabel.style.position = 'absolute';
                annotationLabel.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
                annotationLabel.style.padding = '8px';
                annotationLabel.style.borderRadius = '8px';
                annotationLabel.style.boxShadow = '0px 4px 8px rgba(0, 0, 0, 0.3)';
                annotationLabel.style.fontFamily = 'Arial, sans-serif';
                annotationLabel.style.fontSize = '12px';
                annotationLabel.style.display = 'none';
                annotationLabel.innerText = annotationData.text;
                document.body.appendChild(annotationLabel);

                const position3 = new THREE.Vector3(annotationData.position.x, annotationData.position.y, annotationData.position.z);
                annotations.push({ position: position3, text: annotationData.text, marker: marker, label: annotationLabel });

                updateAnnotationLabelPosition(annotationLabel, position3);

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${annotationData.position.x}</td>
                    <td>${annotationData.position.y}</td>
                    <td>${annotationData.position.z}</td>
                    <td>${annotationData.text}</td>
                    <td><button class="btn btn-danger delete-annotation-btn">Elimina</button></td>
                `;
                annotationsTableBody.appendChild(row);

                // Aggiungi evento click per eliminare l'annotazione
                row.querySelector('.delete-annotation-btn').addEventListener('click', () => {
                    deleteAnnotation({ position: position3, text: annotationData.text, marker: marker, label: annotationLabel });
                });
            });

            animate();
        });
    });
}

// Funzione per aggiungere annotazioni al modello al clic del mouse
function addAnnotation(event) {
    const rect = viewer.getBoundingClientRect();
    const mouseX = ((event.clientX - rect.left) / viewer.clientWidth) * 2 - 1;
    const mouseY = -((event.clientY - rect.top) / viewer.clientHeight) * 2 + 1;

    // Usa il raycaster per verificare se siamo sopra un oggetto
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera({ x: mouseX, y: mouseY }, camera);
    const rayIntersects = raycaster.intersectObject(model, true);

    if (rayIntersects.length > 0) {
        const intersectedPoint = rayIntersects[0].point;
        const annotationText = prompt("Inserisci un'annotazione per questo punto:");
        if (annotationText) {

            // Aggiungi un marcatore visivo (sfera) al punto annotato
            const markerGeometry = new THREE.TorusGeometry(0.05, 0.02, 16, 100);
            const markerMaterial = new THREE.MeshStandardMaterial({ color: 0xff0000, metalness: 0.6, roughness: 0.2 });
            const marker = new THREE.Mesh(markerGeometry, markerMaterial);
            marker.position.copy(intersectedPoint);
            scene.add(marker);

            // Aggiungi l'annotazione al modello
            const annotationLabel = document.createElement('div');
            annotationLabel.className = 'annotation-label';
            annotationLabel.style.position = 'absolute';
            annotationLabel.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
            annotationLabel.style.padding = '8px';
            annotationLabel.style.borderRadius = '8px';
            annotationLabel.style.boxShadow = '0px 4px 8px rgba(0, 0, 0, 0.3)';
            annotationLabel.style.fontFamily = 'Arial, sans-serif';
            annotationLabel.style.fontSize = '12px';
            annotationLabel.style.display = 'none'; // Nascondi l'etichetta inizialmente
            annotationLabel.innerText = annotationText;
            document.body.appendChild(annotationLabel);

            const position3 = new THREE.Vector3(intersectedPoint.x, intersectedPoint.y, intersectedPoint.z);

            annotations.push({ position: position3, text: annotationText, marker: marker, label: annotationLabel });
            saveAnnotations();

            // Aggiorna la posizione dell'etichetta
            updateAnnotationLabelPosition(annotationLabel, intersectedPoint);

            // Aggiungi l'annotazione alla tabella
            const annotationsTableBody = document.querySelector('#annotationsTable tbody');
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${intersectedPoint.x}</td>
                <td>${intersectedPoint.y}</td>
                <td>${intersectedPoint.z}</td>
                <td>${annotationText}</td>
                <td><button class="btn btn-danger delete-annotation-btn">Elimina</button></td>
            `;
            annotationsTableBody.appendChild(row);

            // Aggiungi evento click per eliminare l'annotazione dalla tabella
            row.querySelector('.delete-annotation-btn').addEventListener('click', () => {
                deleteAnnotation({ position: position3, text: annotationText, marker: marker, label: annotationLabel });
            });
        }
    }
}

// Funzione per aggiornare la posizione delle etichette delle annotazioni
function updateAnnotationLabelPosition(label, position) {
    const vector = position.clone().project(camera);
    const x = (vector.x * 0.5 + 0.5) * viewer.clientWidth + viewer.getBoundingClientRect().left;
    const y = (-vector.y * 0.5 + 0.5) * viewer.clientHeight + viewer.getBoundingClientRect().top;
    label.style.left = `${x}px`;
    label.style.top = `${y}px`;
}
// Aggiungi listener per il clic del mouse per aggiungere annotazioni
viewer.addEventListener('dblclick', addAnnotation);

// Funzione di animazione
async function saveAnnotationsToDatabase(checksum, annotationData) {
    console.log('Salvataggio delle annotazioni:', annotationData);
    try {
        const response = await fetch('/src/save_annotation.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ checksum, annotations: annotationData }),
        });
        if (!response.ok) {
            throw new Error('Errore durante il salvataggio delle annotazioni');
        }
        console.log(JSON.stringify({ checksum, annotations: annotationData }));
    } catch (error) {
        console.error('Errore nel salvataggio delle annotazioni:', error);
    }
}

async function fetchAnnotationsFromDatabase(checksum) {
    try {
        const response = await fetch(`/src/get_annotations.php?checksum=${checksum}`);
        if (!response.ok) {
            throw new Error('Errore durante il recupero delle annotazioni');
        }
        const data = await response.json();
        return data.annotations;
    } catch (error) {
        console.error('Errore nel recupero delle annotazioni:', error);
        return [];
    }
}


// Funzione per salvare le annotazioni nel database

function saveAnnotations() {
    console.log('Salvataggio delle annotazioni:', annotations);
    const checksum = document.getElementById('fileInput').dataset.checksum;
    if (!checksum) return;
    const annotationData = annotations.map(({ position, text }) => ({ position, text }));
    saveAnnotationsToDatabase(checksum, annotationData);
}

document.getElementById('saveAnnotation').addEventListener('click', function () {
    saveAnnotations();
});

document.getElementById('saveIIIF').addEventListener('click', function () {
    exportIIIF();
});

function generateIIIFManifest(manifestData) {
    const manifest = {
        "@context": [
            "http://www.w3.org/ns/anno.jsonld",
            "http://iiif.io/api/presentation/3/context.json"
        ],
        "id": manifestData.id || `https://cosme.unicampania.it/rasta/iiifmanifests/${manifestData.canvasName}/${manifestData.canvasName}.json`,
        "type": "Manifest",
        "items": [
            {
                "id": `https://cosme.unicampania.it/rasta/iiifmanifests/${manifestData.canvasName}/${manifestData.canvasName}.json/canvas/0`,
                "type": "Canvas",
                "items": [
                    {
                        "id": `https://cosme.unicampania.it/rasta/iiifmanifests/${manifestData.canvasName}/${manifestData.canvasName}.json/canvas/0/annotationpage/0`,
                        "type": "AnnotationPage",
                        "items": [
                            {
                                "id": `https://cosme.unicampania.it/rasta/iiifmanifests/${manifestData.canvasName}/${manifestData.canvasName}.json/canvas/0/annotation/0`,
                                "type": "Annotation",
                                "motivation": "painting",
                                "body": {
                                    "id": `https://cosme.unicampania.it/rasta/montepugliano/${manifestData.fileName}.glb`,
                                    "type": "Model",
                                    "format": "model/gltf-binary",
                                    "label": {
                                        "@none": [manifestData.modelLabel || "_model"]
                                    }
                                },
                                "target": `https://cosme.unicampania.it/rasta/montepugliano/${manifestData.canvasName}.json/canvas/0`
                            }
                        ]
                    }
                ],
                "annotations": [
                    {
                        "id": `https://cosme.unicampania.it/rasta/montepugliano/${manifestData.canvasName}.json/canvas/0/annotations`,
                        "type": "AnnotationPage",
                        "items": manifestData.annotations.map((annotation, index) => ({
                            "id": `https://cosme.unicampania.it/rasta/montepugliano/${manifestData.canvasName}.json/canvas/0/annotation/${index + 1}`,
                            "type": "Annotation",
                            "motivation": "supplementing",
                            "body": {
                                "type": "TextualBody",
                                "value": annotation.text,
                                "format": "text/plain",
                                "language": "it"
                            },
                            "target": {
                                "type": "SpecificResource",
                                "source": `https://cosme.unicampania.it/rasta/montepugliano/${manifestData.canvasName}.json/canvas/0`,
                                "selector": {
                                    "type": "FragmentSelector",
                                    "value": `xyz=${annotation.x},${annotation.y},${annotation.z}`
                                }
                            }
                        }))
                    }
                ],
                "label": {
                    "@none": [manifestData.canvasLabel || "_example"]
                }
            }
        ],
        "label": {
            "@none": [manifestData.manifestLabel || "3D Example"]
        }
    };

    return JSON.stringify(manifest, null, 2); // Converte l'oggetto in JSON ben formattato
}

function exportIIIF() {
    const fileInput = document.getElementById('fileInput');
    const fileName = fileInput.files[0]?.name.replace('.glb', '');
    const canvasName = fileName || "default_canvas";
    const annotationsData = annotations.map(({ position, text }) => ({
        x: position.x,
        y: position.y,
        z: position.z,
        text: text || ""
    }));

    const manifestData = {
        id: `https://cosme.unicampania.it/rasta/iiifmanifests/${canvasName}/${canvasName}.json`,
        fileName: fileName,
        canvasName: canvasName,
        modelLabel: "_astronaut",
        canvasLabel: "_example",
        manifestLabel: "3D Example",
        annotations: annotationsData
    };

    const manifestJSON = generateIIIFManifest(manifestData);
    console.log(manifestJSON);
    // Salva il file GLB e il manifest sul server
    saveFilesToServer(fileInput.files[0], manifestJSON, fileName);
}

async function saveFilesToServer(glbFile, manifestJSON, fileName) {
    const formData = new FormData();
    formData.append("glbFile", glbFile, `${fileName}.glb`);
    formData.append("manifestJSON", new Blob([manifestJSON], { type: "application/json" }), `${fileName}.json`);

    try {
        const response = await fetch('/src/save_files.php', {
            method: 'POST',
            body: formData
        });
        const exportLinkDiv = document.getElementById("export-link");

        if (response.ok) {
            console.log("File GLB e manifest JSON salvati con successo sul server.");
            exportLinkDiv.innerHTML = `<div style="border: 1px solid #ddd; padding: 10px; margin-top: 10px;"><p>Link al manifest IIIF:</p><textarea rows="2" style="width: 100%; resize: none;" readonly>https://cosme.unicampania.it/rasta/iiifmanifests/${fileName}/${fileName}.json</textarea></div>`;
        } else {
            console.error("Errore durante il salvataggio dei file sul server.");
            exportLinkDiv.innerHTML = `<div style="border: 1px solid #ddd; padding: 10px; margin-top: 10px;"><p>Link al manifest IIIF:</p><textarea rows="2" style="width: 100%; resize: none;" readonly>Errore nella generazione del Manifest</textarea></div>`;

        }
    } catch (error) {
        console.error("Errore nella richiesta di salvataggio dei file:", error);
    }
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);

    // Aggiorna la posizione delle etichette delle annotazioni
    annotations.forEach(annotation => {
        const { label, marker } = annotation;

        // Aggiorna la posizione dell'etichetta in base alla posizione del marker
        updateAnnotationLabelPosition(label, marker.position);

        // Mostra l'etichetta solo se il marcatore è visibile nella scena
        const frustum = new THREE.Frustum();
        const cameraViewProjectionMatrix = new THREE.Matrix4();
        camera.updateMatrixWorld();
        cameraViewProjectionMatrix.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
        frustum.setFromProjectionMatrix(cameraViewProjectionMatrix);
        label.style.display = frustum.containsPoint(marker.position) ? 'block' : 'none';
    });
}