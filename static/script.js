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

    case "
}