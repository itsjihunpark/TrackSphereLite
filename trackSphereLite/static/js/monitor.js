$(document).ready(function () {
  $.get("/metric_calculation/single_metric_from_pickle", (json) => {
    if (json["golfball"] != null) {
      $("div.results").append($("<h4>Metrics</h4>"));
      $("div.results").append($('<div class="tabularMetrics"></div>'));
      $("div.results").append(
        $(
          '<button type="button" class="btn btn-success" id="trajectory-toggle">toggle trajectory view</button>'
        )
      );
      $("div.results").append($('<div id="trajectory"></div>'));

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
              $("button#llm-modal-btn").remove();
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
              $("div.results").append(
                $(
                  '<button type="button" id="llm-modal-btn" class="btn btn-info ml-1" data-toggle="modal" data-target="#llm-modal">Launch your AI golf coach</button>'
                )
              );

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
  $("img#video").on("error", function () {
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
        $(
          '<h2 style="color: green">' +
            json["message"] +
            " (" +
            json["distance"] +
            "m)" +
            "</h2>"
        )
      );
    } else {
      $("div#initial_positioning_aid").empty();
      $("div#initial_positioning_aid").append(
        $(
          '<h2 style="color: red">' +
            json["message"] +
            " (" +
            json["distance"] +
            "m)" +
            "</h2>"
        )
      );
    }
  });
  socket.on("initial_ball_position_verification", (json) => {
    $("div#initial_positioning_aid").empty();
    $("div.results").empty();
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
  try {
    const img = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");

    let isDrawing = false;
    let startX = 0,
      startY = 0;

    let selected = false;
    img.onload = () => {
      if (selected == false) {
        // Set canvas size to match the image
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;

        // Draw the image on the canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        selected = true;
      } else {
      }
    };

    canvas.addEventListener("mousedown", (e) => {
      startX = e.offsetX;
      startY = e.offsetY;
      isDrawing = true;
    });

    canvas.addEventListener("mousemove", (e) => {
      if (!isDrawing) return;

      const currentX = e.offsetX;
      const currentY = e.offsetY;

      // Clear canvas and redraw image
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      //ctx.drawImage(img, 0, 0);

      // Draw current rectangle
      ctx.beginPath();
      ctx.strokeStyle = "red";
      ctx.lineWidth = 2;
      ctx.rect(startX, startY, currentX - startX, currentY - startY);
      ctx.stroke();
    });

    canvas.addEventListener("mouseup", (e) => {
      if (!isDrawing) return;
      isDrawing = false;

      const endX = e.offsetX;
      const endY = e.offsetY;

      const x1 = Math.min(startX, endX);
      const y1 = Math.min(startY, endY);
      const x2 = Math.max(startX, endX);
      const y2 = Math.max(startY, endY);

      console.log(
        `Rectangle coordinates: x1=${x1}, y1=${y1}, x2=${x2}, y2=${y2}`
      );

      bbox_width = x2 - x1;
      bbox_height = y2 - y1;

      centre_x = x1 + bbox_width / 2;
      centre_y = y1 + bbox_height / 2;

      width_normalised = bbox_width / canvas.width;
      height_normalised = bbox_height / canvas.height;
      centre_x_normalised = 1 - centre_x / canvas.width;
      centre_y_normalised = centre_y / canvas.height;

      socket.emit("target_selection", {
        centre_x: centre_x_normalised,
        centre_y: centre_y_normalised,
        w: width_normalised,
        h: height_normalised,
      });
    });
    socket.on("selected_target", (json) => {
      console.log(json["message"]);
      if (json["system_ready"]) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    });
    socket.on("target_position", (json) => {
      data = {
        name: "target",
        type: "scatter3d",
        mode: "marker",
        marker: {
          color: "rgb(255, 0, 0)",
          size: 4,
        },
        x: [json["x"]],
        y: [json["z"]],
        z: [0],
        showlegend: false,
      };

      Plotly.plot("trajectory-live", [data]);
    });
  } catch (err) {
    console.log("to debug later sorry future jihun:(");
  }
  $("#myModal").on("shown.bs.modal", function () {
    $("#myInput").trigger("focus");
  });
});
