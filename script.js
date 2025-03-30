
const brokerUrl = "wss://test.mosquitto.org:8081"; 
const topic = "<your_course_code>/<your_name>/my_temperature"; 


let client;
let isConnected = false; 


function startConnection() {
  const host = document.getElementById("mqttHost").value;
  const port = document.getElementById("mqttPort").value;
  if (!host || !port) {
    alert("Please enter both MQTT broker host and port.");
    return;
  }
  
  client = new Paho.MQTT.Client(`ws://${host}:${port}/mqtt`, 'web-client-' + Math.random().toString(16).substr(2, 8));
  
  client.onConnectionLost = onConnectionLost;
  client.onMessageArrived = onMessageArrived;
  
  const options = {
    onSuccess: onConnect,
    onFailure: onFailure,
    useSSL: port === "8081" ? true : false 
  };

  client.connect(options);
  isConnected = true;
  
  document.getElementById("mqttHost").disabled = true;
  document.getElementById("mqttPort").disabled = true;
  document.getElementById("startBtn").disabled = true;
  document.getElementById("endBtn").disabled = false;
}


function endConnection() {
  if (isConnected) {
    client.disconnect();
    isConnected = false;
    document.getElementById("mqttHost").disabled = false;
    document.getElementById("mqttPort").disabled = false;
    document.getElementById("startBtn").disabled = false;
    document.getElementById("endBtn").disabled = true;
    
    
    locationMarker.setLatLng([51.0447, -114.0719]);
    locationMarker.setStyle({
      fillColor: 'gray', 
      color: '#000',
      weight: 1,
      opacity: 1,
      fillOpacity: 0.8
    });
    locationMarker.bindPopup("Waiting for location update...");
  }
}

function onConnect() {
  console.log("Connected to MQTT broker");
  client.subscribe(topic);
}

function onFailure(error) {
  console.log("Failed to connect: " + error.errorMessage);
  alert("MQTT connection failed: " + error.errorMessage);
}

function onConnectionLost(responseObject) {
  if (responseObject.errorCode !== 0) {
    console.log("Disconnected: " + responseObject.errorMessage);
    alert("Disconnected from broker. Reconnecting...");
    setTimeout(() => { startConnection(); }, 3000);
  }
}


function onMessageArrived(message) {
  console.log("Message received:", message.payloadString);
  try {
    const geoJson = JSON.parse(message.payloadString);
    const lat = geoJson.geometry.coordinates[1];
    const lon = geoJson.geometry.coordinates[0];
    const temp = parseFloat(geoJson.properties.temperature);

  
    locationMarker.setLatLng([lat, lon]);
    locationMarker.bindPopup("Temperature: " + temp + "°C");
    locationMarker.setStyle({ fillColor: getTemperatureColor(temp) });
  } catch (e) {
    console.error("Error parsing message:", e);
  }
}

// Return a color based on the temperature
function getTemperatureColor(temp) {
  if (temp < 10) return 'blue';
  if (temp < 30) return 'green';
  return 'red';
}


function shareStatus() {
  if (!isConnected) {
    alert("Please start the MQTT connection first.");
    return;
  }
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(publishLocation, handleGeoError, { enableHighAccuracy: true, maximumAge: 0 });
  } else {
    alert("Geolocation is not supported by this browser.");
  }
}

function publishLocation(position) {
  const latitude = position.coords.latitude;
  const longitude = position.coords.longitude;
  const temperature = (Math.random() * 100 - 40).toFixed(2); 
  
  const geoJson = {
    type: "Feature",
    geometry: {
      type: "Point",
      coordinates: [longitude, latitude]
    },
    properties: {
      temperature: temperature
    }
  };
  
  const message = new Paho.MQTT.Message(JSON.stringify(geoJson));
  message.destinationName = topic;
  client.send(message);
  alert(`Status shared:\nLocation: (${latitude.toFixed(5)}, ${longitude.toFixed(5)})\nTemperature: ${temperature}°C`);
}

function handleGeoError(error) {
  console.error("Geolocation error: " + error.message);
  alert("Error getting geolocation: " + error.message);
}


function publishCustomMessage() {
  if (!isConnected) {
    alert("Please start the MQTT connection first.");
    return;
  }
  const topicCustom = document.getElementById("topicInput").value;
  const msgCustom = document.getElementById("messageInput").value;
  if (!topicCustom || !msgCustom) {
    alert("Please enter both topic and message.");
    return;
  }
  const message = new Paho.MQTT.Message(msgCustom);
  message.destinationName = topicCustom;
  client.send(message);
  alert("Message published to " + topicCustom);
}


const map = L.map('map').setView([51.0447, -114.0719], 13);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);


const locationMarker = L.circleMarker([51.0447, -114.0719], {
  radius: 10,
  fillColor: 'gray', 
  color: '#000',
  weight: 1,
  opacity: 1,
  fillOpacity: 0.8
}).addTo(map);
locationMarker.bindPopup("Waiting for location update...");
