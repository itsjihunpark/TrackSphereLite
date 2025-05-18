$(document).ready(function () {
  selected = $("textarea#selected_csv").val(); // selects hidden text field with a csv of metric_ids
  url = "/metric_calculation/metrics";
  data = JSON.stringify({ metric_id_list: selected });
  req = post(url, data);
  req.then((json) => {
    generateTable(json);
    retrieveAndGenerateTrajectory(json, selected);
  });
});
