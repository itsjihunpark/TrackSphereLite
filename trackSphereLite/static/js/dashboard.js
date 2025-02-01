$(document).ready(function () {
  selected = $("textarea#selected_csv").val(); // selects hidden text field with a csv of metric_ids
  url = get_url() + "/api/metrics";
  data = JSON.stringify({ metric_id_list: selected });
  req = post(url, data);
  req.success((json) => {
    generateTable(json);
    retrieveAndGenerateTrajectory(json, selected);
  });
});
