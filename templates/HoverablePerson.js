// HoverablePerson.js
export class HoverablePerson {
    constructor(scene, raycaster) {
        this.scene = scene;
        this.raycaster = raycaster;
        this.hoverableObjects = [];
    }

    createPerson(position = [0, 0, 0], personData = {}) {
        const person = new THREE.Group();

        // Body
        const bodyGeometry = new THREE.BoxGeometry(0.4, 0.54, 0.2);
        const bodyMaterial = new THREE.MeshPhongMaterial({ color: 0x1e90ff });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        body.position.y = 0.25;
        person.add(body);

        // Head
        const headGeometry = new THREE.SphereGeometry(0.15);
        const headMaterial = new THREE.MeshPhongMaterial({ color: 0xffd700 });
        const head = new THREE.Mesh(headGeometry, headMaterial);
        head.position.y = 0.65;
        person.add(head);

        // Arms
        const armGeometry = new THREE.BoxGeometry(0.1, 0.3, 0.1);
        const armMaterial = new THREE.MeshPhongMaterial({ color: 0x1e90ff });
        const leftArm = new THREE.Mesh(armGeometry, armMaterial);
        leftArm.position.set(-0.25, 0.35, 0);
        leftArm.rotation.z = -Math.PI / 6;
        person.add(leftArm);

        const rightArm = new THREE.Mesh(armGeometry, armMaterial);
        rightArm.position.set(0.25, 0.35, 0);
        rightArm.rotation.z = Math.PI / 6;
        person.add(rightArm);

        // Legs
        const legGeometry = new THREE.BoxGeometry(0.15, 0.3, 0.15);
        const legMaterial = new THREE.MeshPhongMaterial({ color: 0x000080 });
        const leftLeg = new THREE.Mesh(legGeometry, legMaterial);
        leftLeg.position.set(-0.1, -0.15, 0.1);
        leftLeg.rotation.x = -Math.PI / 2;
        person.add(leftLeg);

        const rightLeg = new THREE.Mesh(legGeometry, legMaterial);
        rightLeg.position.set(0.1, -0.15, 0.1);
        rightLeg.rotation.x = -Math.PI / 2;
        person.add(rightLeg);

        // Add userData and position
        person.userData = { ...personData, isHoverable: true };
        person.position.set(...position);
        
        // Add to scene and hoverable objects
        this.scene.add(person);
        this.hoverableObjects.push(person);

        return person;
    }

    checkHover(mouse, camera) {
        this.raycaster.setFromCamera(mouse, camera);
        const intersects = this.raycaster.intersectObjects(this.hoverableObjects, true);

        if (intersects.length > 0) {
            let userObject = intersects[0].object;
            while (userObject.parent && !userObject.userData.name) {
                userObject = userObject.parent;
            }

            if (userObject.userData.name) {
                return userObject.userData;
            }
        }
        return null;
    }

    updateInfoPanel(hoverData, infoPanel) {
        if (hoverData) {
            infoPanel.innerHTML = `<h3>${hoverData.name}</h3><p>${hoverData.bio}</p>`;
            infoPanel.style.display = 'block';
        } else {
            infoPanel.style.display = 'none';
        }
    }
}

// Usage example:
/*
// In your main script:
const hoverablePerson = new HoverablePerson(scene, raycaster);

// Create multiple people
personas.forEach((persona, index) => {
    if (index < positions.length) {
        hoverablePerson.createPerson(positions[index], persona);
    }
});

// In your animation loop:
function animate() {
    requestAnimationFrame(animate);
    
    const hoverData = hoverablePerson.checkHover(mouse, camera);
    hoverablePerson.updateInfoPanel(hoverData, infoPanel);
    
    renderer.render(scene, camera);
}
*/