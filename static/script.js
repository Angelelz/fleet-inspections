switch (window.location.pathname) {
    // If page is index
    case "/": {
        // Just need to make sure tables fit in width of screen
        // To do that, calculate minimum width of users' table and set media query
        window.onload = function() {
            let root = document.documentElement;
            var table = document.getElementById('index-users');
            if (table) {
                var originalWidth = table.style.width;
                table.style.width = '1px';
                const smallestWidth = table.getBoundingClientRect().width + 24;
                table.style.width = originalWidth;
                smalestWidthText = "(max-width: " + Math.floor(smallestWidth) + "px)";

                var x = window.matchMedia(smalestWidthText);

                function handleTabletChange(e) {
                    // Check if the media query is true
                    if (e.matches) {
                        var tds = document.getElementsByClassName("email-tohide");

                        for (var i = 0; i < tds.length; ++i) {
                            tds[i].style.display = "none";
                        }
                        document.getElementById("head-to-hide").style.display = "none";
                    }
                    else {
                        var tds = document.getElementsByClassName("email-tohide");
                        for (var i = 0; i < tds.length; ++i) {
                            tds[i].style.display = "table-cell";
                        }
                        document.getElementById("head-to-hide").style.display = "table-cell";
                    }
                }

                x.addListener(handleTabletChange);
                handleTabletChange(x);
            }

        }
        break;
    }

    case "/inspection": {
        function showHide(obj) {
            radio = document.getElementById(obj.name);
            if (radio.checked) {
                document.getElementById(obj.name + "_t").style = "visibility: visible;";
            }
            else {
                document.getElementById(obj.name + "_t").style = "visibility: hidden;";
            }
        }
        break;
    }

    case "/vehicles": {
        window.onload = function () {
            var myChart;
            const OPTIONS = { year: 'numeric', month: 'short', day: 'numeric' };
            const TODAY = Date.parse(Date());
            const OFFSET = new Date().getTimezoneOffset() * 60000;
            let input = document.querySelector('select');
            if (input) {
                input.addEventListener('change', async function(e) {

                    var url = new URL(window.location.href);
                    var search_params = url.searchParams;
                    search_params.set('vehicle', encodeURIComponent(e.target.value));
                    let response = await fetch('/vehicles', {
                        method: 'POST',
                        body: 'vehicle=' + encodeURIComponent(e.target.value),
                        headers: {
                            'Content-type': 'application/x-www-form-urlencoded'
                        },
                        credentials: 'include',
                    });
                    let vehicles = await response.json();
                    let html = '';
                    for (let v in vehicles) {
                        html += '<tr><td>' + vehicles[v][3] + '</td><td>' + vehicles[v][2] + '</td><td>' + vehicles[v][1] + '</td><td>' + vehicles[v][0] + '</td></tr>';
                    }
                    document.getElementById('toChange').innerHTML = html;
                    url.search = search_params.toString();
                    history.pushState(null, document.title, url);
                    document.getElementById('titleToChange').innerHTML = "Vehicle " + e.target.value + ": Latest issues";
                    myChart.destroy();
                    do_graph();
                });
            }
            window.addEventListener('popstate', function () {
                window.location = location.href;
            });
            async function graph() {
                let response = await fetch('/vehicles', {
                    method: 'POST',
                    credentials: 'include',
                });
                let all_inspections = await response.json();
                return all_inspections;
            }
            function do_graph() {
                graph().then(
                    function(value) {
                        var url = new URL(window.location.href);
                        var search_params = url.searchParams;
                        var dataset = [];
                        var storage = [];
                        for(var j=0;j<value.length;j++) {

                            for(var i=0;i<value[j][Object.keys(value[j])[0]]['dates'].length;i++)
                            {
                                x = value[j][Object.keys(value[j])[0]]['dates'][i] + OFFSET;
                                y = value[j][Object.keys(value[j])[0]]['miles'][i];
                                if (x != 0 || y != 0) {
                                    var json = {x: x, y: y};
                                    storage.push(json);
                                }
                            }
                            if (storage.length > 0) {
                                vehicle = 'vehicle ' + Object.keys(value[j])[0]
                                var randomColor = Math.floor(Math.random()*16777215).toString(16);
                                randomColor = '#' + randomColor;
                                var obj = {label: vehicle, data: storage, fill: false, backgroundColor: randomColor, borderColor: randomColor, showLine: true};
                                storage = [];
                                if (search_params.has('vehicle')) {
                                    if (search_params.get('vehicle') == Object.keys(value[j])[0]) {
                                        dataset.push(obj);
                                    }
                                }
                                else {
                                    dataset.push(obj);
                                }

                            }

                        }
                        const ctx = document.getElementById('myChart');
                        const data = {
                            datasets: dataset,
                        };
                        const config = {
                            type: 'scatter',
                            plugins: ['chartjs-plugin-annotation'],
                            data: data,
                            options: {
                                plugins: {
                                    tooltip: {
                                        callbacks: {
                                            label: function(context) {
                                                var label = context.dataset.label || '';
                                                if ((context.dataset.data.length - 1 == context.dataIndex) && context.dataset.data.length > 1) {
                                                    label += ' oil change projection';
                                                }
                                                if (label) {
                                                    label += ': (' + context.parsed.y + ' miles : ';
                                                }
                                                else {
                                                    label += '(' + context.parsed.y + ' miles : ';
                                                }
                                                d = new Date(context.parsed.x)
                                                label += d.toLocaleDateString('en-US', OPTIONS) + ')';
                                                return label;
                                            }
                                        }
                                    },
                                    autocolors: false,
                                    annotation: {
                                        annotations: [{
                                            type: 'line',
                                            xMin: TODAY,
                                            xMax: TODAY,
                                            label: {
                                                content: "TODAY",
                                                enabled: true,
                                                position: "start",
                                            }
                                        }]
                                    },
                                },

                                scales: {
                                    x: {
                                        type: 'linear',
                                        title: {
                                            display: true,
                                            text: 'Date',
                                        },
                                        position: 'bottom',
                                        ticks: {
                                            callback: function(val, index) {
                                                d = new Date(val)
                                                return d.toLocaleDateString('en-US', OPTIONS);
                                            },
                                            maxRotation: 0,
                                            autoSkipPadding: 8,
                                        }
                                    },
                                    y: {
                                        title: {
                                            display: true,
                                            text: 'Mileage',
                                        }
                                    }
                                },
                                elements: {
                                    point: {
                                        radius: 6,
                                    }
                                }
                            }
                        };
                        myChart = new Chart(
                            document.getElementById('myChart'),
                            config
                        );

                    }
                );
            }
            do_graph();
        }
        break;
    }

    case "/add-vehicle": {
        window.onload = function() {
            var _scannerIsRunning = false;

            function startScanner() {
                Quagga.init({
                    inputStream: {
                        name: "Live",
                        type: "LiveStream",
                        target: document.querySelector('#scanner-container'),
                        constraints: {
                            width: 2048,
                            height: 1536,
                            facingMode: "environment"
                        },
                    },
                    decoder: {
                        readers: [
                            "code_128_reader",
                            "code_39_reader",
                            "code_39_vin_reader"
                        ],
                        debug: {
                            showCanvas: true,
                            showPatches: true,
                            showFoundPatches: true,
                            showSkeleton: true,
                            showLabels: true,
                            showPatchLabels: true,
                            showRemainingPatchLabels: true,
                            boxFromPatches: {
                                showTransformed: true,
                                showTransformedBox: true,
                                showBB: true
                            }
                        }
                    },
                    //locate: false,
                    numOfWorkers: 1,
                }, function (err) {
                    if (err) {
                        console.log(err);
                        return
                    }
                    console.log("Initialization finished. Ready to start");
                    if (!_scannerIsRunning) {
                        Quagga.start();
                        // Set flag to is running
                        _scannerIsRunning = true;
                    }
                });
                Quagga.onProcessed(function (result) {
                    var drawingCtx = Quagga.canvas.ctx.overlay,
                    drawingCanvas = Quagga.canvas.dom.overlay;
                    if (result) {
                        if (result.boxes) {
                            drawingCtx.clearRect(0, 0, parseInt(drawingCanvas.getAttribute("width")), parseInt(drawingCanvas.getAttribute("height")));
                            result.boxes.filter(function (box) {
                                return box !== result.box;
                            }).forEach(function (box) {
                                Quagga.ImageDebug.drawPath(box, { x: 0, y: 1 }, drawingCtx, { color: "green", lineWidth: 2 });
                            });
                        }
                        if (result.box) {
                            Quagga.ImageDebug.drawPath(result.box, { x: 0, y: 1 }, drawingCtx, { color: "#00F", lineWidth: 2 });
                        }
                        if (result.codeResult && result.codeResult.code) {
                            Quagga.ImageDebug.drawPath(result.line, { x: 'x', y: 'y' }, drawingCtx, { color: 'red', lineWidth: 3 });
                        }
                    }
                });
                Quagga.onDetected(function (result) {
                    Quagga.stop();
                    document.getElementById("scanner-container").innerHTML = "<p>VIN detected</p>";
                    _scannerIsRunning = false;
                    console.log("Barcode detected and processed : [" + result.codeResult.code + "]", result.code);
                    document.getElementById("vin").value = result.codeResult.code;
                    $.ajax({
                        url: "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/" + result.codeResult.code + "?format=json",
                        type: "GET",
                        dataType: "json",
                        success: function(result)
                        {
                            document.getElementById("scanner-container").innerHTML = "<p>VIN decoded sucessfully</p>";
                            document.getElementById("year").value = result.Results[9].Value;
                            document.getElementById("make").value = result.Results[6].Value;
                            document.getElementById("model").value = result.Results[8].Value;
                        },
                        error: function(xhr, ajaxOptions, thrownError)
                        {
                            document.getElementById("scanner-container").innerHTML = "<p>An error was encountered while trying to decode your VIN, see Console for details.</p>";
                            console.log(xhr.status);
                            console.log(thrownError);
                        }
                    });
                });
            }
            // Start/stop scanner
            document.getElementById("btn").addEventListener("click", function () {
                if (_scannerIsRunning) {
                    _scannerIsRunning = false;
                    document.getElementById("scanner-container").style.display = "none";
                    Quagga.stop();
                } else {
                    document.getElementById("scanner-container").style.display = "block";
                    startScanner();
                }
            }, false);
        }
        break;
    }
}