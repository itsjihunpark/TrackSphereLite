$(document).ready(function () {
  $("img#video").error(() => {
    $(this).hide();
  });
  const socket = io();
  socket.on("frame", (jpg) => {
    document.getElementById("video").src = "data:image/jpeg;base64," + jpg;
  });
  socket.on("initial_ball_position_verification", (json) => {
    console.log(json);
    selected_club = $("select#club").children("option:selected").val();
    save_results = $("#save_results").is(":checked");
    console.log(selected_club, save_results);
  });

  selected_club = null;
  $("button#confirm_options").click(function () {
    selected_club = $("select#club").children("option:selected").val();
    if (selected_club == "") {
      alert("select a club");
    } else {
      //run when a golf club is selected
      save_results = $("#save_results").is(":checked");
      console.log(save_results, selected_club);
      $("div#preview_stream").empty();
      // make a call to start recording video for x amount and analyse
      url = "/camera_controls/start_monitor";
      data = JSON.stringify({
        selected_club: { selected_club },
        save_metric: { save_results },
      });
      set_monitoring_mode_req = post(url, data);
      set_monitoring_mode_req.then(function (json) {
        console.log(json);
      });
    }
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
