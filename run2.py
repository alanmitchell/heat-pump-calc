from heatpump import app2

# Need the host argument below to run on the Pixelbook.  Should still
# run correctly elsewhere.
app2.app.run_server(debug=True, host='0.0.0.0')
