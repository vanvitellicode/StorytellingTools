
var random=0;
var angle = 0; // Angolo iniziale (in radianti)
var radius = 3; // Raggio dell'orbita (distanza dal centro dell'oggetto)
var centerX = 0; // Coordinata X del centro del modello
var centerY = 0; // Altezza del modello
var centerZ = 0; // Coordinata Z del centro del modello


function getVector(camera, targetObject) {
    var entityPosition = new THREE.Vector3();
    targetObject.object3D.getWorldPosition(entityPosition);

    var cameraPosition = new THREE.Vector3();
    camera.object3D.getWorldPosition(cameraPosition);
    var vector = new THREE.Vector3(entityPosition.x, entityPosition.y, entityPosition.z);
    vector.subVectors(cameraPosition, vector).add(cameraPosition);
    return vector;
}

function centerCamera(camera, vector) {
    //Based on: https://codepen.io/wosevision/pen/JWRMyK
    camera.object3D.lookAt(vector);
    camera.object3D.updateMatrix();

    //Based on: https://stackoverflow.com/questions/36809207/aframe-threejs-camera-manual-rotation
    var rotation = camera.getAttribute('rotation');
    camera.components['look-controls'].pitchObject.rotation.x = THREE.Math.degToRad(rotation.x);
    camera.components['look-controls'].yawObject.rotation.y = THREE.Math.degToRad(rotation.y);
}

function lookObj(cameraId, targetId) {
    var cameraEl = document.getElementById(cameraId);
    cameraEl.setAttribute("look-controls", { enabled: false });
    let pointTarget = getVector(cameraEl, document.getElementById(targetId));
    centerCamera(cameraEl, pointTarget);
    cameraEl.setAttribute("look-controls", { enabled: true });
}



async function getMyPosition() {
    try {
        const response = await fetch('api-service/position?id=1'); // Aspetta la risposta della fetch
        if (!response.ok) {
            throw new Error(`Errore nella richiesta: ${response.status} - ${response.statusText}`);
        }
        return await response.json(); // Aspetta la conversione della risposta in JSON e assegna alla variabile
    } catch (error) {
        console.error('Errore:', error); // Gestione errori
        return null; // Restituisce null in caso di errore
    }
}


function setBleCamera(){
    const camera = document.querySelector('#myCamera');
    getMyPosition().then((position) => {
        console.log(position);
        camera.setAttribute('position', {x: 5*(position.y-2.2), y: 0, z: 5*(position.x-0.4)});
        
        // Usa lookAt per far sì che la fotocamera guardi sempre verso il centro dell'oggetto (coordinates: centerX, centerY, centerZ)
        lookObj('cam', 'model');
        // Aumenta l'angolo per far ruotare la fotocamera
        angle += 0.01; // Regola questo valore per controllare la velocità di rotazione (più basso è più lento)

        // Assicurati che l'angolo non cresca indefinitamente (reset ogni giro completo)
        if (angle >= 2 * Math.PI) {
            angle = 0; // Reset angolo dopo un giro completo
        }
    });


    /*
    if(random==0)
        camera.setAttribute('position', {x: camera.object3D.position.x, y: camera.object3D.position.y, z: camera.object3D.position.z+1});
    else
        camera.setAttribute('position', {x: camera.object3D.position.x, y: camera.object3D.position.y, z: camera.object3D.position.z-1});

     random = (random+1)%2;
    */
}

setInterval(() => {
    //currentLon += step; // Move slightly east
    setBleCamera();
  }, 500); // Every 3 seconds






