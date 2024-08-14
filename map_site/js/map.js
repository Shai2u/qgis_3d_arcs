API_KEY = "khvVGD9ThOCYQHMkBNt5";

mapboxgl.accessToken =
  "pk.eyJ1Ijoic2hhaXN1c3NtYW4iLCJhIjoiY2w2OW1sNnQ5MDR1bDNjbjFzMnQzdzViaCJ9.lFrtxuzxqkAaGMxJK3xw9w";
var centerPoint = [34.5, 32];
var lngLat = [0, 0];
var map = new mapboxgl.Map({
  container: "map",
  style: `https://api.maptiler.com/maps/streets-v2/style.json?key=${API_KEY}`, // stylesheet location
  center: centerPoint, // starting position [lng, lat]
  zoom: 9, // starting zoom
});

// Add the GeoJSON lines layer
map.on("load", function () {
  map.addSource("line-source", {
    type: "geojson",
    data: "../all_missles_3d.geojson", // Replace with the path to your GeoJSON file
  });

  map.addLayer({
    id: "line-layer",
    type: "line",
    source: "line-source",
    paint: {
      "line-color": "#000000",
      "line-width": 2,
    },
  });
});
