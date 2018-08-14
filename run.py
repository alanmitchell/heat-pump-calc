from heatpump import app

# Need the host argument below to run on the Pixelbook.  Should still
# run correctly elsewhere.
app.app.run_server(debug=True, host='0.0.0.0')
