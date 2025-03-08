$(document).ready(function () {
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

    setTimeout(() => {
      video_previewer.empty();
      $("div.user_monitor_option_input").empty();
      video_previewer.append($('<span class="loader_analysing"></span>'));
      video_previewer.append($("<h2>Shot recorded. Analysing...</h2>"));
    }, 3000);
  });
  socket.on("analysis_result", (json) => {
    console.log(json);
    video_previewer.empty();
    //location.reload();
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
