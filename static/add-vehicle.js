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