$(document).ready(function () {
  $.get("/metric_calculation/single_metric_from_pickle", (json) => {
    if (json["golfball"] != null) {
      $("div.results").append($("<h2>Swing metrics</h2>"));
      $("div.results").append($('<div class="tabularMetrics"></div>'));
      $("div.results").append($("<h2>Trajectory</h2>"));
      $("div.results").append($('<div id="trajectory"></div>'));

      console.log(json["golfball"]["metric"]);
      console.log(json["golfball"]["trajectory"]);

      generateTable(json["golfball"]["metric"]);
      generateTrajectoryPlot(json["golfball"]["trajectory"]);
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
  socket.on("initial_ball_position_verification", (json) => {
    console.log(json);

    setTimeout(() => {
      $("div.results").empty();
      video_previewer.empty();
      $("div.user_monitor_option_input").empty();
      video_previewer.append($('<span class="loader_recording"></span>'));
      video_previewer.append(
        $(
          "<h2>Ball position verified. Recording started. Take your shot...</h2>"
        )
      );
    }, 3000);
  });
  socket.on("recording_status", (json) => {
    console.log(json);
    video_previewer.empty();
    $("div.user_monitor_option_input").empty();
    video_previewer.append($('<span class="loader_analysing"></span>'));
    video_previewer.append($("<h2>Shot recorded. Analysing...</h2>"));
  });
  socket.on("analysis_status", (json) => {
    console.log(json);
    video_previewer.empty();
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
