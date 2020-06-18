document.addEventListener("DOMContentLoaded", function(){
    var mymap = L.map('mapid').setView([51.505, -0.09], 13);

    L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        maxZoom: 18,
        id: 'mapbox/dark-v10',
        tileSize: 512,
        zoomOffset: -1,
        accessToken: 'pk.eyJ1IjoiZGVhZHdhdHIiLCJhIjoiY2p5dWJid3B3MGJ5cDNucnJiamQ3c2VubiJ9.dNV9fXFWNnRdNkLAZ-6t1g'
    }).addTo(mymap);

// var marker = L.marker([51.5, -0.09]).addTo(mymap);
// marker.bindPopup("<b>Hello world!</b><br>I am a popup.");

    const COLORS = {
        'truck': 'rgba(255, 99, 132, 0.7)',
        'car': 'rgba(255, 206, 86, 0.7)',
        'motorbike': 'rgba(75, 192, 192, 0.7)',
        'bus': 'rgba(153, 102, 255, 0.7)',
        'person': 'rgba(255, 159, 64, 0.7)'
    };

    function updateGraph(e) {
        config.options.title.text = 'Loading ' + this.options.id.replace("JamCams_", "") + "...";
        config.data.labels = [];
        config.data.datasets = [];
        window.myChart.update();
        fetch('http://51.105.7.82:8080/api/v1/cams/recent?id=' + this.options.id.replace("JamCams_", ""))
            .then(function (response) {
                response.json().then(function (result) {
                    // console.log(result);
                    config.data.labels = result.dates.map(d => {
                        return (new Date(d))
                    });
                    // console.log(config.data.labels)
                    config.data.datasets = [];
                    for (type in result.counts) {
                        config.data.datasets.push(
                            {
                                label: type,
                                backgroundColor: COLORS[type],
                                borderColor: COLORS[type],
                                data: result.counts[type],
                                fill: false,
                            }
                        )
                    }
                    config.options.title.text = 'Counts for camera ' + this.options.id.replace("JamCams_", "") + ' (last 12 hrs)';
                    window.myChart.update()
                });
            });
    }

    fetch('https://api.tfl.gov.uk/Place/Type/JamCam/')
        .then(function (response) {
            response.json().then(function (result) {
                for (let c of result) {
                    // console.log(c)
                    L.marker([c.lat, c.lon], options = {'id': c.id}).addTo(mymap).bindPopup(
                        "<strong>" + c.id + "</strong>" +
                        "<br>" +
                        "<img src='https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/" + c.id.replace("JamCams_", "") + ".jpg' alr='" + c.id + "' width='281' height='230'>" +
                        "<br><div class='mono'>" +
                        "<span style='color: red'>Calibration in queue</span><br>" +
                        "h &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Height (metres): <br>" +
                        "phi &nbsp;&nbsp;&nbsp; | Heading (degrees): <br>" +
                        "u_0,v_0 | Vanishing point (pixels):  <br>" +
                        "S &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Scale factor (NA): </div>"
                    )
                        .on('click', updateGraph);
                }
            });
        });

    var ctx = document.getElementById('myChart').getContext('2d');
    var config = {
        type: 'scatter',
        data: {
            labels: ['None'],
            datasets: []
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Click on a camera to see counts within last 12 hrs'
            },
            tooltips: {
                mode: 'index',
                intersect: false,
                bodyFontColor: '#000',
                titleFontColor: '#000',
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            scales: {
                xAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Time'
                    },
                    type: 'time',
                    // distribution: 'linear',
                    time: {
                        parser: 'MM/DD/YYYY HH:mm',
                        tooltipFormat: 'll HH:mm',
                        unit: 'hour',
                        unitStepSize: 1,
                        displayFormats: {
                            'hour': 'HH:mm'
                        }
                    }
                }],
                yAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Counts'
                    },
                    ticks: {
                        min: 0,
                        beginAtZero: true,
                        stepSize: 1,
                    }
                }]
            }
        }
    };
    window.myChart = new Chart(ctx, config);
});