$(document).ready(function () {
  selected_club = null;
  $("button#confirm_options").click(function () {
    selected_club = $("select#clubs").children("option:selected").val();
    if (selected_club == "") {
      alert("select a club");
    } else {
      //run when a golf club is selected
      save_results = $("#save_results").is(":checked");
      console.log(save_results, selected_club);
      url = "/api/set_monitor_mode";
      data = JSON.stringify({
        selected_club: { selected_club },
        save_metric: { save_results },
      });
      set_monitoring_mode_req = post(url, data);
      set_monitoring_mode_req.then(function (json) {
        //runs if golf ball is in correct position
        console.log(json);
        console.log("setting recording mode");
        url = "/api/set_record_mode";
        data = JSON.stringify({
          some_data: "some_data",
        });
        set_recording_mode_req = post(url, data);
        set_recording_mode_req.then(function (json) {
          //runs once the video analysis is complete
          console.log(json);
          //simulating a click
          //$("button#confirm_options").click();
        });
      });
    }
  });

  selected = "1";
  url = "/api/metrics";
  data = JSON.stringify({ metric_id_list: selected });
  req = post(url, data);
  req.success((json) => {
    generateTable(json);
    retrieveAndGenerateTrajectory(json, selected);
  });
  return true;
});
