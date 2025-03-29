// Predefined MQTT Broker Details
const brokerUrl = "wss://test.mosquitto.org:8081"; // WebSocket URL of the broker
const topic = "<your_course_code>/<your_name>/my_temperature"; // Replace with your actual topic

let client;
let isConnected = false; // Track connection state

// Start MQTT connection
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
    useSSL: port === "8081" ? true : false // use SSL if port is 8081
  };

  client.connect(options);
  isConnected = true;
  
  document.getElementById("mqttHost").disabled = true;
  document.getElementById("mqttPort").disabled = true;
  document.getElementById("startBtn").disabled = true;
  document.getElementById("endBtn").disabled = false;
}

// End MQTT connection and reset app state
function endConnection() {
  if (isConnected) {
    client.disconnect();
    isConnected = false;
    document.getElementById("mqttHost").disabled = false;
    document.getElementById("mqttPort").disabled = false;
    document.getElementById("startBtn").disabled = false;
    document.getElementById("endBtn").disabled = true;
    
    // Reset the marker to its initial state (centered on Calgary)
    locationMarker.setLatLng([51.0447, -114.0719]);
    locationMarker.setStyle({
      fillColor: 'gray', // default color
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

// Handle incoming MQTT messages
function onMessageArrived(message) {
  console.log("Message received:", message.payloadString);
  try {
    const geoJson = JSON.parse(message.payloadString);
    const lat = geoJson.geometry.coordinates[1];
    const lon = geoJson.geometry.coordinates[0];
    const temp = parseFloat(geoJson.properties.temperature);

    // Update marker position and popup with temperature
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

// Share My Status: get geolocation and publish GeoJSON message
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

// Publish location data along with a random temperature
function publishLocation(position) {
  const latitude = position.coords.latitude;
  const longitude = position.coords.longitude;
  const temperature = (Math.random() * 100 - 40).toFixed(2); // Random temperature between -40 and 60
  
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

// Publish a custom message to any topic
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

// Initialize Leaflet.js map centered on Calgary
const map = L.map('map').setView([51.0447, -114.0719], 13);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Use a circle marker instead of an icon marker
const locationMarker = L.circleMarker([51.0447, -114.0719], {
  radius: 10,
  fillColor: 'gray', // default color
  color: '#000',
  weight: 1,
  opacity: 1,
  fillOpacity: 0.8
}).addTo(map);
locationMarker.bindPopup("Waiting for location update...");
