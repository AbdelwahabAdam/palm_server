def pshell_setup(env):
    request = env['request']
    env['dbsession'] = request.dbsession
    env['tm'] = request.tm
