//helper function
function generateTable(json) {
  //takes an array of json objects and generates html
  tableContainer = $("div.tabularMetrics");
  tableContainer.empty();

  //column heading
  const columns = [
    "Shot",
    "Distance (m)",
    "Speed (kph)",
    "Launch angle",
    "Time",
    "club",
  ];
  //column data keys
  const keys = [
    "distance",
    "velocity",
    "ball_launch_angle",
    "swing_event_timestamp",
    "type_of_club",
  ];
  table = $("<table></table>");
  column_heading = $("<tr></tr>");
  columns.forEach(function (column) {
    column_heading.append($("<th>" + column + "</th>"));
  });
  table.append(column_heading);
  for (i = 0; i < json.length; i++) {
    row = $("<tr></tr>");
    row.append($("<td>" + (i + 1) + "</td>"));
    for (j = 0; j < keys.length; j++) {
      row.append($("<td>" + json[i][keys[j]] + "</td>"));
    }
    table.append(row);
    tableContainer.append(table);
  }
}

function retrieveAndGenerateTrajectory(json, selected) {
  data = JSON.stringify({
    metric_id_list: selected,
  });
  url = "/metric_calculation/trajectory";
  result = post(url, data).then((json) => {
    generateTrajectoryPlot(json);
  });
}

function generateTrajectoryPlot(json) {
  console.log("generating", json);
  all_shots = [];
  for (i = 0; i < json.length; i++) {
    shot = {
      name: "shot " + (i + 1),
      type: "scatter3d",
      mode: "lines",
      x: json[i]["x"],
      y: json[i]["y"],
      z: json[i]["z"],
    };
    all_shots.push(shot);
  }

  club = $("select#club").val();
  if (club !== undefined) {
    console.log(club);
    if (club == "p") {
      //layout option 1
      xrange = [-2, 2];
      yrange = [0, 4];
      zrange = [0, 4];
    } else {
      //layout option 2
      xrange = [-15, 15];
      yrange = [0, 50];
      zrange = [0, 30];
    }
  } else {
    club = $("tr")[1].children[5].innerHTML;
    if (club == "p") {
      //layout option 1
      xrange = [-2, 2];
      yrange = [0, 4];
      zrange = [0, 4];
      console.log(club);
    } else {
      //layout option 2
      xrange = [-15, 15];
      yrange = [0, 50];
      zrange = [0, 30];
    }
  }
  // https://community.plotly.com/t/is-it-possible-to-limit-the-x-y-z-axis-of-a-3d-surface-plot/34118
  layout = {
    margin: {
      l: 0,
      r: 0,
      b: 0,
      t: 0,
    },
    scene: {
      camera: {
        eye: { x: 0, y: -3, z: 1 },
      },
      xaxis: { range: xrange },
      yaxis: { range: yrange },
      zaxis: { range: zrange },
    },
  };
  Plotly.newPlot("trajectory", all_shots, layout, { displayModeBar: false });
}

function post(url, data) {
  return $.ajax({
    url: url,
    type: "POST",
    data: data,
    dataType: "json",
    contentType: "application/json",
    success: function (json) {},
    timeout: 0,
  }).fail(function () {
    console.log("failed");
  });
}
