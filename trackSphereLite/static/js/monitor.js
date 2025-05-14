$(document).ready(function () {
  $.get("/metric_calculation/single_metric_from_pickle", (json) => {
    if (json["golfball"] != null) {
      $("div.results").append($("<h2>Swing metrics</h2>"));
      $("div.results").append($('<div class="tabularMetrics"></div>'));
      $("div.results").append($("<h2>Trajectory</h2>"));
      $("div.results").append(
        $('<button id="trajectory-toggle">toggle trajectory view</button>')
      );
      $("div.results").append($('<div id="trajectory"></div>'));

      console.log(json["golfball"]["metric"]);
      console.log(json["golfball"]["trajectory"]);

      generateTable(json["golfball"]["metric"]);
      generateTrajectoryPlot(json["golfball"]["trajectory"]);
      let current_trajectory_only = true;

      $("button#trajectory-toggle").click(() => {
        current_trajectory_only = !current_trajectory_only;
        console.log(current_trajectory_only);
        if (current_trajectory_only) {
          post(
            "/metric_calculation/metric_from_pickle",
            JSON.stringify({
              message: "single",
            })
          ).then((json) => {
            if (json["golfball"] != null) {
              $("div#trajectory").remove();
              $("div.results").append($('<div id="trajectory"></div>'));
              generateTable(json["golfball"]["metric"]);
              generateTrajectoryPlot(json["golfball"]["trajectory"]);
            }
          });
        } else {
          post(
            "/metric_calculation/metric_from_pickle",
            JSON.stringify({
              message: "all",
            })
          ).then((json) => {
            if (json["golfball"] != null) {
              $("div#trajectory").remove();
              $("div.results").append($('<div id="trajectory"></div>'));
              generateTable(json["golfball"]["metric"]);
              generateTrajectoryPlot(json["golfball"]["trajectory"]);
            }
          });
        }
      });
    }
    return true;
  });

  $("img#video").error(() => {
    $(this).hide();
  });
  var video_previewer = $("div#preview_stream");
  const socket = io();
  socket.on("frame", (jpg) => {
    document.getElementById("video").src = "data:image/jpeg;base64," + jpg;
  });
  socket.on("initial_positioning_aid", (json) => {
    console.log(json["message"], json["distance"]);
    if (json["message"] == "correct position") {
      $("div#initial_positioning_aid").empty();
      $("div#initial_positioning_aid").append(
        $('<h2 style="color: green">Correct position</h2>')
      );
    } else {
      $("div#initial_positioning_aid").empty();
      $("div#initial_positioning_aid").append(
        $(
          '<h2 style="color: red">' +
            json["message"] +
            " (" +
            json["distance"] +
            "m )" +
            "</h2>"
        )
      );
    }
  });
  socket.on("initial_ball_position_verification", (json) => {
    $("div#initial_positioning_aid").empty();
    $("div#initial_positioning_aid").append(
      $('<h2 style="color: green">Tracking</h2>')
    );
    generateLiveTrajectoryPlot();
  });
  socket.on("analysing", (json) => {
    var data_update = {
      x: [[json["x"]]],
      y: [[json["z"]]],
      z: [[json["y"]]],
    };
    console.log(data_update);
    Plotly.extendTraces("trajectory-live", data_update, [0]);
  });
  socket.on("analysis_completed", (json) => {
    location.reload();
  });

  /**
  selected = "1";
  url = "/metric_calculation/metrics";
  data = JSON.stringify({ metric_id_list: selected });
  req = post(url, data);
  req.success((json) => {
    generateTable(json);
    retrieveAndGenerateTrajectory(json, selected);
  });
  return true;
   */
});
