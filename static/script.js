switch (window.location.pathname) {
    case "/": {
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
}