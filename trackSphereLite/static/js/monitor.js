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
  });
  socket.on("recording_status", (json) => {
    console.log(json);
    //location.reload();
  });
  socket.on("analysis_result", (json) => {
    console.log(json);
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
