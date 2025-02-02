$(document).ready(function () {
  $.get("/api/metrics", (json) => {
    generateTable(json);
    handleCheckboxEvent();
    generateFilters(json);
    handleFilterEvent(json);
    return true;
  }).fail(function () {
    console.log("None returned"); // DEBUG MESSAGE
  });
});

//helper function
function generateTable(json) {
  //takes an array of json objects and generates html
  tableContainer = $("div.tabularMetrics");
  tableContainer.empty();

  //column heading
  const columns = [
    "Select",
    "club",
    "Distance (m)",
    "Speed (kph)",
    "Timestamp",
  ];
  table = $("<table></table>");
  column_heading = $("<tr></tr>");
  columns.forEach(function (column) {
    column_heading.append($("<th>" + column + "</th>"));
  });
  table.append(column_heading);

  //column data
  const keys = [
    "type_of_club",
    "distance",
    "velocity",
    "swing_event_timestamp",
  ];

  for (i = 0; i < json.length; i++) {
    row = $("<tr></tr>");
    row.append(
      $(
        '<td><input class="selection" type="checkbox" id=' +
          json[i].golfball_id +
          "></td>"
      )
    );
    for (j = 0; j < keys.length; j++) {
      row.append($("<td>" + json[i][keys[j]] + "</td>"));
    }
    table.append(row);

    tableContainer.append(table);
  }
}
function generateFilters(json) {
  filterContainer = $("div.filters");
  filterContainer.empty();
  filterContainer.append(
    $('<button type="button" class="filter" id="none">None</button>')
  );
  clubs = [];
  for (i = 0; i < json.length; i++) {
    idx = clubs.indexOf(json[i].type_of_club);
    if (idx == -1) {
      clubs.push(json[i].type_of_club);
      filterContainer.append(
        $(
          '<button type="button" class="filter" id="' +
            json[i].type_of_club +
            '">' +
            json[i].type_of_club +
            "</button>"
        )
      );
    }
  }
}
function handleFilterEvent(json) {
  $("button.filter").click(function () {
    $("form.viewInDetailOption").empty();
    filtered = json;

    clubToFilter = $(this).attr("id");
    if (clubToFilter != "none") {
      filtered = $.grep(json, function (row, i) {
        return row.type_of_club === clubToFilter;
      });
    }

    generateTable(filtered);
    handleCheckboxEvent();
  });
}
function handleCheckboxEvent() {
  selected = [];
  //wait until all table is generated
  $("input.selection").change(function () {
    metricID = $(this).attr("id");
    if ($(this).is(":checked")) {
      selected.push(metricID);
    } else {
      idxToRemove = selected.indexOf(metricID);
      selected.splice(idxToRemove, 1);
    }
    optionToViewSelectedInDetail(selected);
  });
}
function optionToViewSelectedInDetail(selected) {
  viewInDetailOption = $("form.viewInDetailOption");
  viewInDetailOption.empty();
  if (selected.length != 0) {
    if (selected.length == 1) {
      buttontext = "View Selected";
    } else {
      buttontext = "Compare Selected";
    }

    selectedcsv = $(
      '<textarea name="selected_csv" id="selected_csv" hidden>' +
        selected +
        "</textarea>"
    );

    submission = $('<input type="submit" value="' + buttontext + '">');

    viewInDetailOption.append(selectedcsv);
    viewInDetailOption.append(submission);
    console.log(buttontext);
    console.log(selected);
  } else {
    console.log("none selected");
    console.log(selected);
  }
}
