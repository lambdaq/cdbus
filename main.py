from bottle import Bottle, run, static_file, response, abort, error

from scrapper import Transit

app = Bottle()

@app.route('/')
@error(404)
def index():
    return "Hello busfags. This little app for collecting historical & realtime CDBus data."

@app.route('/<bus_no>')
def show_bus_info(bus_no):
    bus = Transit(bus_no)
    fmt = '%s, %s, %s'
    result = '%s\n' % bus_no
    r = bus.last_stop('17082410', 6 )
    print r
    result += '\n'.join([fmt % x for x in r])
    result += '\n'
    r = bus.last_stop('17082411', 14)
    print r
    result += '\n'.join([fmt % x for x in r])
    response.content_type = 'text/plain; charset=utf-8'
    print 'tada'
    return result

@app.route('/x')
def x():
    bus = Transit(56)
    print bus.last_stop('17082410', 6 )
    print bus.last_stop('17082411', 14)

    

@app.route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root='/path/to/your/static/files')


#run(app, host='0.0.0.0', port=8001)