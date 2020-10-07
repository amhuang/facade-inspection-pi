/*
MQTT Javascript Client
*/

var mqtt = function() {

    /* ----- Global Variables ----- */

    var DOM = {};

    var client;
    var minPress = 300;         // min ms to hold for key/mouse
    var firstPress = true;      // limit keypress to firing only once
    var holdTimeout;            // delays hoist operation by minPress
    var indivHoistMode = false;
    var levelingEnabled = true;
    var movingInterval;         // sends msgs while arrows held down at sendFreq
    var sendFreq = 1000;        // how often msg sent (hoist checks level)

    var initAltitude = 0;       // the offset set by zeroAltitude
    var currAltitude = 0;

    var connectedNoMsg;         // interval reconnect tried when no message received
    var reconnectAttempt = 0;   // only equals 0 the first time GUI is loaded
    var timeFromGnd = 0;        // sec from ground determined from fromGndTimers
    var fromGndTimer;            // interval to keep track off timeFromGnd
    var recoverTimeFromGnd;     // interval that sends time from ground on disconnect
    var cycleTimer;             // times active duty time

    /* ----- Initializing Functions ----- */

    function cache() {

        if (sessionStorage.getItem("upper-ip") != null) {
            $('#upperpi').val(sessionStorage.getItem("upper-ip"));
        } if (sessionStorage.getItem("lower-ip") != null) {
            $('#lowerpi').val(sessionStorage.getItem("lower-ip"));
        } if (sessionStorage.getItem("backup-ip") != null) {
            $('#backuppi').val(sessionStorage.getItem("backup-ip"));
        }

        DOM.document = $(document);
        DOM.host = $('#upperpi').val();
        DOM.port = 9001;

        DOM.upArrow = $('#up-arrow');
        DOM.downArrow = $('#down-arrow');
        DOM.upLeftBox = $("#up-left-box");
        DOM.upRightBox = $("#up-right-box");
        DOM.downLeftBox = $("#down-left-box");
        DOM.downRightBox = $("#down-right-box");
        DOM.hoistMode = $("#hoist-mode");

        DOM.popupError = $("#popup-error");
        DOM.popupConfirm = $("#popup-confirm");
        DOM.popupSettings = $('#popup-settings');
        DOM.errorMsg = $('#error-msg');
        DOM.confirmMsg = $('#confirmation-msg');
        DOM.confirmHeader = $("#confirmation-header");
        DOM.closeError = $('#close-error');

        DOM.confirmYes = $('#confirm-yes');
        DOM.confirmNo = $('#confirm-no');

        DOM.angle = $('#angle');
        DOM.altitude = $('#altitude');
        DOM.temperature = $('#temperature');
        DOM.pressure = $('#pressure');
        DOM.angleAnimation = $("#angle-animation");
        DOM.zeroAngle = $('#zero-angle');
        DOM.zeroAltitude = $('#zero-altitude');

        DOM.showSettings = $('#show-settings');
        DOM.closeSettings = $('#close-settings');
        DOM.makeLevel = $('#make-level');
        DOM.toggleLeveling = $('#toggle-leveling');
        DOM.noLeveling = $("#no-leveling");
        DOM.switchBackup = $("#switch-backup");
        DOM.replaceWithBackup = $("#replace-with-backup");
        DOM.timeFromGnd = $('#time-from-ground');
        DOM.resetIpAddr = $('#set-ip-addr');
    }

    // This method gets called in mqttConnect(), not init()
    function bindEvents() {
        // Hoist control buttons/listeners
        DOM.document.on({
            keydown: keyPress,
            keyup: keyRelease
        });
        DOM.upArrow.on({
            mousedown: arrowPress.bind(DOM.upArrow, "Up"),
            mouseup: arrowRelease.bind(DOM.upArrow)
        });
        DOM.downArrow.on({
            mousedown: arrowPress.bind(DOM.downArrow, "Down"),
            mouseup: arrowRelease.bind(DOM.downArrow)
        });
        DOM.upRightBox.on({
            mousedown: arrowPress.bind(DOM.upRightBox, "Up right"),
            mouseup: arrowRelease.bind(DOM.upRightBox.children())
        });
        DOM.upLeftBox.on({
            mousedown: arrowPress.bind(DOM.upLeftBox.children(), "Up left"),
            mouseup: arrowRelease.bind(DOM.upLeftBox.children())
        });
        DOM.downRightBox.on({
            mousedown: arrowPress.bind(DOM.downRightBox.children(), "Down right"),
            mouseup: arrowRelease.bind(DOM.downRightBox.children())
        });
        DOM.downLeftBox.on({
            mousedown: arrowPress.bind(DOM.downLeftBox.children(), "Down left"),
            mouseup: arrowRelease.bind(DOM.downLeftBox.children())
        });
        DOM.hoistMode.on('click', toggleHoistMode);

        // Settings and options
        DOM.makeLevel.on('click', makeLevel);
        DOM.toggleLeveling.on('click', toggleLeveling);

        // Zeroing data
        DOM.zeroAngle.on('click', zeroAngle);
        DOM.zeroAltitude.on('click', zeroAltitude);

        // Error popup and options
        DOM.closeError.on('click', closeError);
        DOM.noLeveling.on('click', accelerometerError.bind(null, 'Ignore angle'));
        DOM.switchBackup.on('click', accelerometerError.bind(null, 'Switch to backup'));
    }

    function bindSettings() {
        DOM.confirmNo.on('click', function() {
            DOM.popupConfirm.hide()
        });
        DOM.showSettings.on('click', toggleSettings);
        DOM.closeSettings.on('click', toggleSettings);
        DOM.replaceWithBackup.on('click', connectBackupPi);
        DOM.resetIpAddr.on('click', resetIpAddr);
    }

    function mqttConnect() {
        var clientId = "gui"+new Date().getTime();
        client = new Paho.MQTT.Client(DOM.host, DOM.port, clientId);
        client.onConnectionLost = onConnectionLost;
        client.onMessageArrived = onMessageArrived;

        console.log('Connecting to: ' + DOM.host + ' on port: ' + DOM.port);

        var options = {
            timeout: 3,
            onSuccess: onConnect,
            onFailure: onFailure,
            keepAliveInterval: 5,
            willMessage: newMsg('Off', 'hoist')
        };
        client.connect(options);
    }

    /* ----- MQTT Callback & Helper Functions ----- */

    function onConnect() {
        // Adds ready to go note to popup

        client.subscribe("status");
        client.subscribe("accelerometer/angle");
        client.subscribe("altimeter/altitude");
        client.subscribe("altimeter/pressure");
        client.subscribe("altimeter/temperature");

        // Can only send msgs in onConnect, so event listeners here
        bindEvents();

        // Retrieves in case of page refresh (last time received from Pi)
        timeFromGnd = sessionStorage.getItem('time-from-ground');
        displayTime(timeFromGnd, DOM.timeFromGnd);

        //
        connectedNoMsg = setTimeout(function() {
            onFailure();
            console.log('no message received');
        }, 4000);

        // Sends last stored timeFromGnd continuously in case of disconnect
        recoverTimeFromGnd = setInterval( function() {
            client.send(newMsg(timeFromGnd.toString(), 'time/fromground'));
            console.log('sending ', timeFromGnd.toString());
        }, 200);
    }

    function onMessageArrived(message)  {
        clearTimeout(connectedNoMsg);
        clearInterval(recoverTimeFromGnd);
        client.subscribe('time/fromground');

        if ( reconnectAttempt > 0 ) {
            DOM.errorMsg.append("<br><br>Reconnected. Hoist ready for operation.");
            DOM.closeError.show();
            DOM.replaceWithBackup.hide();
            reconnectAttempt = 0;
            console.log('reconnected');
        }

        var msg = message.payloadString;
        var topic = message.destinationName;
        if (topic == "status") {
            if (msg == "Upper Pi client disconnected") {
                console.log(msg);
                client.unsubscribe('time/fromground');
                reconnect();
            }
        } else if (topic == "accelerometer/angle") {
            renderAccelerometerData(msg);
        } else if (topic == "altimeter/altitude") {
            renderAltimeterData(DOM.altitude, msg);
        } else if (topic == "altimeter/temperature") {
            renderAltimeterData(DOM.temperature, msg);
        } else if (topic == "altimeter/pressure") {
            renderAltimeterData(DOM.pressure, msg);
        } else if (topic == "time/fromground") {
            timeFromGnd = Number(msg);
            console.log('time from ground received: ' + timeFromGnd);
            sessionStorage.setItem("time-from-ground", timeFromGnd);
            displayTime(timeFromGnd, DOM.timeFromGnd);
        }
    }

    function onFailure() {
        console.log('on failure');
        reconnect();
    }

    function onConnectionLost(responseObject) {
        console.log('Connection lost');
        console.log(responseObject);
        if (responseObject.errorCode == 5){
            location.reload();
        }
        else {
            reconnect();
        }
    }

    function reconnect() {
        if (reconnectAttempt == 0) {
            DOM.popupError.show();
            DOM.replaceWithBackup.show();
            DOM.closeError.hide();
            DOM.noLeveling.hide();
            reconnectAttempt++;
        }
        console.log('reconnecting');
        DOM.errorMsg.html("Hoist controls disconnected. Reconnect attempt: " + reconnectAttempt);
        reconnectAttempt++;
        mqttConnect();
    }

    function newMsg(message, topic) {
        var msg = new Paho.MQTT.Message(message);
        msg.destinationName = topic;
        return msg;
    }

    function connectBackupPi() {
        /* Sets mqtt-ip in HTML to IP address of backup Pi */
        DOM.host = $('#backuppi').val();
        DOM.errorMsg.append("<br><br>Connecting to backup...");
        mqttConnect();
    }


    /* ----- Sensor Data Rendering ----- */

    // Processes accelerometer data from MQTT messages and displays it
    function renderAccelerometerData(msg) {
        if ( msg == "Disconnected" ) {
            console.log(msg);
            DOM.errorMsg.html("The accelerometer is disconnected. If you continue, there will be no leveling.");
            DOM.popupError.show();
            DOM.closeError.show();
            DOM.noLeveling.show();
            DOM.switchBackup.show();
            DOM.replaceWithBackup.hide();

            DOM.angle.html("Disconnected");
            DOM.angleAnimation.css({
                '-webkit-transform': 'rotate(0deg)',
                'transform': 'rotate(0deg)',
                'background': 'grey'
            });
        } else {
            msg = Number(msg).toFixed(1);
            DOM.angle.html(msg + "&deg");
            rotateAnimation(msg);
        }
    }

    // Processes altimeter data from MQTT messages and displays it
    function renderAltimeterData(typeDisplay, msg) {
        var unit, nullVal;
        var type = typeDisplay.attr("id");
        msg = Number(msg);

        if (isNaN(msg) || msg == nullVal) {
            typeDisplay.html("Disconnected");
            return;
        } else if (type == "altitude") {
            unit = " ft";
            nullVal = -676.9
            currAltitude = msg * 3.281;
            msg = (currAltitude - initAltitude).toFixed(2);
            if (msg < 2 && msg > 1) {
                closeToGround(msg, 'feet')
            }
        } else if (type == "temperature") {
            unit = "&degF";
            nullVal = -212.3;
        } else if (type == "pressure") {
            unit = " hPa";
            nullVal = 1100;
        }
        typeDisplay.html(msg + unit);
    }

    // Rotates the bar animation
    function rotateAnimation(degrees) {
        if (degrees > 25 || degrees < -25) {
            DOM.angleAnimation.css({'background': '#ff8a65'});
        } else if (degrees > 2 || degrees < -2) {
            DOM.angleAnimation.css({
                '-webkit-transform': 'rotate('+degrees+'deg)',
                'transform': 'rotate('+degrees+'deg)',
                'background': '#ffe680'
            });
        } else {
            DOM.angleAnimation.css({
                '-webkit-transform': 'rotate('+degrees+'deg)',
                'transform': 'rotate('+degrees+'deg)',
                'background': '#a5d6a7'
            });
        }
    }


    /* ----- Event Handlers ----- */

    function keyPress(event) {
        if ( firstPress && !indivHoistMode ) {
            firstPress = false;

            if (event.key == "ArrowUp") {
                // timeout forces key to be held for minPress to run
                holdTimeout = setTimeout( function() {
                    DOM.upArrow.addClass('active');
                    // sends initial message
                    client.send(newMsg('Up', 'hoist'));
                    console.log("Up");

                    // sends subsequent messages in intervals of sendFreq ms
                    movingInterval = setInterval( function() {
                        client.send(newMsg('Up', 'hoist'));
                        console.log("Up");
                    }, sendFreq);

                    // starts timer counting up
                    timer('Up');
                }, minPress);
            }
            else if (event.key == "ArrowDown") {
                holdTimeout = setTimeout( function() {
                    DOM.downArrow.addClass('active');
                    client.send(newMsg('Down', 'hoist'));
                    console.log("Down");
                    movingInterval = setInterval( function() {
                        client.send(newMsg('Down', 'hoist'));
                        console.log("Down");
                    }, sendFreq);
                    timer('Down');
                }, minPress);
            }

        }
    }

    function keyRelease(event) {
        clearTimeout(holdTimeout);
        clearInterval(movingInterval);
        firstPress = true;

        if ( (event.key == "ArrowUp" || event.key == "ArrowDown") &&
                !indivHoistMode ) {
            client.send(newMsg('Off', 'hoist'));
            DOM.upArrow.removeClass('active');
            DOM.downArrow.removeClass('active');
            timer('Off');
        }
    }

    function arrowPress(message) {
        if (firstPress == true) {
            firstPress = false;

            // timeout forces key to be held for minPress to run
            holdTimeout = setTimeout( function() {
                // sends initial message
                client.send(newMsg(message, 'hoist'));

                // sends subsequent messages in intervals of sendFreq ms
                movingInterval = setInterval( function() {
                    client.send(newMsg(message, 'hoist'));
                    console.log(message);
                }, sendFreq);

                // starts timer counting in whichever direction message sets
                timer(message);
            }, minPress);
            $(this).delay(minPress).addClass('active');
        }
    }

    function arrowRelease() {
        firstPress = true;
        clearTimeout(holdTimeout);
        clearInterval(movingInterval);
        timer('Off');
        client.send(newMsg('Off', 'hoist'));
        console.log('Off');
        $(this).removeClass('active');
    }

    function timer(msg) {
        if (msg == 'Up') {
            fromGndTimer = setInterval(function() {
                timeFromGnd += 1;
                displayTime(timeFromGnd, DOM.timeFromGnd);
            }, 1000);
        } else if (msg == 'Down') {
            fromGndTimer = setInterval(function() {
                timeFromGnd -= 1;
                displayTime(timeFromGnd, DOM.timeFromGnd);
                if (timeFromGnd < 5 && timeFromGnd > 4) {
                    closeToGround(timeFromGnd, 'seconds');
                }
            }, 1000);
        } else if (msg == 'Up left' || msg == 'Up right') {
            fromGndTimer = setInterval(function() {
                timeFromGnd += 0.5;
                displayTime(timeFromGnd, DOM.timeFromGnd);
            }, 1000);
        } else if (msg == 'Down left' || msg == 'Down right') {
            fromGndTimer = setInterval(function() {
                timeFromGnd -= 0.5;
                displayTime(timeFromGnd, DOM.timeFromGnd);
            }, 1000);
        } else if (msg = 'Off') {
            clearInterval(fromGndTimer);
        }
    }

    // Takes time as seconds
    function displayTime(time, text) {
        var min = Math.floor(Math.abs(time)/60);
        var sec = Math.floor(Math.abs(time)%60);
        if (sec < 10) {
            sec = '0' + sec;
        }
        if (time < 0) {
            text.html('-' + min + ':' + sec);
        } else {
            text.html(min + ':' + sec);
        }
    }

    function closeError() {
        DOM.popupError.hide();
        DOM.noLeveling.hide();
        DOM.switchBackup.hide();
        DOM.replaceWithBackup.show();
        DOM.errorMsg.html("");
    }

    function accelerometerError(action) {
        DOM.popupError.hide();
        DOM.noLeveling.hide();
        DOM.switchBackup.hide();
        client.send(newMsg(action, 'accelerometer/status'));
    }

    function toggleHoistMode() {
        client.send(newMsg('Off', 'hoist'));

        DOM.upArrow.removeClass('active');
        DOM.downArrow.removeClass('active');
        DOM.upArrow.toggle();
        DOM.downArrow.toggle();
        DOM.upLeftBox.toggle();
        DOM.upRightBox.toggle();
        DOM.downLeftBox.toggle();
        DOM.downRightBox.toggle();


        if (!indivHoistMode) {
            indivHoistMode = true;
            DOM.hoistMode.children().html('Individual');
        }
        else if (levelingEnabled) {
            indivHoistMode = false;
            DOM.hoistMode.children().html('Leveling');
        }
        else {
            indivHoistMode = false;
            DOM.hoistMode.children().html('No Leveling');
        }
    }

    function toggleSettings() {
        DOM.popupSettings.toggle();
        DOM.popupConfirm.hide();
    }

    function makeLevel() {
        client.send(newMsg('Make level', 'hoist'));
    }

    function toggleLeveling() {
        client.send(newMsg('Toggle leveling', 'hoist'));

        if (levelingEnabled) {
            DOM.toggleLeveling.children().html('Enable leveling');
            DOM.hoistMode.children().html('Not Leveling');
            levelingEnabled = false;
        }
        else {
            DOM.toggleLeveling.children().html('Disable leveling');
            DOM.hoistMode.children().html('Leveling');
            levelingEnabled = true;
        }
    }

    function zeroAngle() {
        DOM.popupSettings.hide();
        DOM.popupConfirm.toggle();

        DOM.confirmMsg.html('Click confirm to zero the angle. The hoist should be on the ground to maximize accuracy.');

        DOM.confirmYes.on('click', function() {
            client.send(newMsg('Zero accelerometer', 'accelerometer/status'));
            DOM.popupConfirm.hide();
        });
    }

    function zeroAltitude() {
        DOM.popupSettings.hide();
        DOM.popupConfirm.toggle();

        DOM.confirmMsg.html('Click confirm to zero the altitude. The hoist should be on the ground to maximize accuracy.');

        DOM.confirmYes.on('click', function() {
            DOM.popupConfirm.hide();
        });
    }

    function closeToGround(value, unit) {
        client.send(newMsg('Off', 'hoist'));
        DOM.popupSettings.hide();
        DOM.popupConfirm.toggle();
        DOM.confirmMsg.html('You are ' + Math.floor(value) + ' ' + unit + ' away from the ground.');
        DOM.confirmHeader.hide();
        DOM.confirmYes.addClass('center');
        DOM.confirmYes.children().html('Continue');
        DOM.confirmNo.hide();

        DOM.confirmYes.on('click', function() {
            DOM.popupConfirm.hide();
            DOM.confirmHeader.show();
            DOM.confirmYes.removeClass('center');
            DOM.confirmYes.children().html('Confirm');
            DOM.confirmNo.show();
        });
    }

    function resetIpAddr(e) {
        e.preventDefault();
        DOM.popupSettings.hide();
        DOM.popupConfirm.toggle();
        DOM.popupConfirm.css({'z-index': '3'});
        DOM.confirmMsg.html('Click confirm to change the IP addresses you are connected to and to and reload the page.');

        DOM.confirmYes.on('click', function() {
            DOM.popupConfirm.hide();
            DOM.popupConfirm.css({'z-index': '1'});
            sessionStorage.setItem("upper-ip", $('#upperpi').val());
            sessionStorage.setItem("lower-ip", $('#lowerpi').val());
            sessionStorage.setItem("backup-ip", $('#backuppi').val());
            location.reload();
        });
    }

    /* ----- PUBLIC METHODS & EXPORT ----- */

    function init() {
        cache();
        bindSettings();
        mqttConnect();
    }

    return {
        init: init
    };
}();