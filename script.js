document.addEventListener("DOMContentLoaded", function () {
    let map = L.map('map').setView([51.0447, -114.0719], 13);

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    let marker = null;
    let watchId = null;
    let client = null;
    let reconnectTimeout = 3000; // 3 seconds
    let isConnected = false;

    // Connect to MQTT
    function connectMQTT() {
        //let mqttHost = document.getElementById("mqttHost").value;
        //let mqttPort = document.getElementById("mqttPort").value;
        let mqttHost = "broker.hivemq.com";
        let mqttPort = 1883;  // Use 1883 for non-secure MQTT


        if (!mqttHost || !mqttPort) {
            alert("Please enter MQTT broker host and port.");
            return;
        }

        client = new Paho.MQTT.Client(mqttHost, Number(mqttPort), "clientId-" + Math.random().toString(16).substr(2, 8));

        client.onConnectionLost = function (responseObject) {
            if (responseObject.errorCode !== 0) {
                alert("Disconnected. Reconnecting...");
                setTimeout(connectMQTT, reconnectTimeout);
            }
        };

        client.connect({
            onSuccess: function () {
                console.log("Connected to MQTT Broker");
                isConnected = true;
                document.getElementById('startTracking').disabled = false;  // Enable Start Tracking
                document.getElementById('shareStatus').disabled = false;   // Enable Share My Status
            },
            onFailure: function (message) {
                alert("Connection failed: " + message.errorMessage);
                setTimeout(connectMQTT, reconnectTimeout);
            }
        });
    }

    // Get marker color based on temperature
    function getMarkerColor(temperature) {
        if (temperature < 10) {
            return 'blue';
        } else if (temperature >= 10 && temperature < 30) {
            return 'green';
        } else {
            return 'red';
        }
    }

    // Start geolocation tracking
    document.getElementById('startTracking').addEventListener('click', function () {
        if (!isConnected) {
            alert("You should connect to MQTT first!");
            return; // Prevent starting tracking until MQTT is connected
        }

        if (navigator.geolocation) {
            watchId = navigator.geolocation.watchPosition(
                function (position) {
                    let lat = position.coords.latitude;
                    let lon = position.coords.longitude;
                    let altitude = position.coords.altitude;  // Get altitude from geolocation

                    if (marker) {
                        marker.setLatLng([lat, lon]);
                    } else {
                        marker = L.marker([lat, lon]).addTo(map)
                            .bindPopup("You are here").openPopup();
                    }

                    map.setView([lat, lon], 13);

                    // Add "Share My Status" button functionality
                    document.getElementById('shareStatus').addEventListener('click', function () {
                        if (marker) {
                            let position = marker.getLatLng();
                            let latitude = position.lat;
                            let longitude = position.lng;

                            // Generate a random temperature between -10 and 50 degrees Celsius
                            let temperature = (Math.random() * 50 - 10).toFixed(2);

                            // Create GeoJSON object with latitude, longitude, temperature, and altitude
                            let geojsonMessage = {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [longitude, latitude]
                                },
                                "properties": {
                                    "temperature": temperature,
                                    "altitude": altitude || "Not available"  // If altitude is not available, show this message
                                }
                            };

                            // Publish the GeoJSON message to MQTT topic
                            if (client && client.isConnected()) {
                                let topic = `your_course_code/your_name/my_temperature`; // Replace with actual course code and name
                                let message = new Paho.MQTT.Message(JSON.stringify(geojsonMessage));
                                message.destinationName = topic;

                                // Publish the message
                                client.send(message);
                                alert(`Status shared: Location (${latitude}, ${longitude}), Temperature: ${temperature}°C, Altitude: ${altitude || "Not available"}`);
                            } else {
                                alert("MQTT not connected. Please connect first.");
                            }
                        } else {
                            alert("Location not available.");
                        }
                    });
                },
                function (error) {
                    alert("Error getting location: " + error.message);
                },
                { enableHighAccuracy: true, maximumAge: 0 }
            );

            document.getElementById("mqttHost").disabled = true;
            document.getElementById("mqttPort").disabled = true;
        } else {
            alert("Geolocation is not supported by this browser.");
        }
    });

    // Stop geolocation tracking
    document.getElementById('stopTracking').addEventListener('click', function () {
        if (watchId !== null) {
            navigator.geolocation.clearWatch(watchId);
            watchId = null;
            alert("Tracking stopped.");
        }

        if (client) {
            client.disconnect();
            alert("MQTT Disconnected.");
        }

        document.getElementById("mqttHost").disabled = false;
        document.getElementById("mqttPort").disabled = false;
    });

    // Subscribing to MQTT topic to update marker color on receiving temperature data
    client.onMessageArrived = function (message) {
        let geojsonMessage = JSON.parse(message.payloadString);
        let temperature = geojsonMessage.properties.temperature;
        let position = geojsonMessage.geometry.coordinates;

        if (marker) {
            let markerColor = getMarkerColor(parseFloat(temperature));

            // Update marker color dynamically based on temperature
            marker.setIcon(L.icon({
                iconUrl: `http://example.com/path/to/${markerColor}_icon.png`, // Modify to use actual URL for different colored icons
                iconSize: [25, 41],  // Adjust size if needed
                iconAnchor: [12, 41], // Anchor the icon to the bottom center
                popupAnchor: [1, -34], // Popup position
            }));

            // Update the popup with the temperature
            marker.setPopupContent(`Temperature: ${temperature}°C`);
        }
    };

    // Enable "Start Tracking" only after connecting to MQTT
    document.getElementById('startTracking').disabled = true;
    document.getElementById('shareStatus').disabled = true;

    // Connect to MQTT on page load
    connectMQTT();
});
