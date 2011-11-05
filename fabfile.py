from fabric.api import env, run
from fabric.context_managers import cd
from fabric.decorators import roles

env.user = 'ubuntu'
env.roledefs.update({
    'app': ['mustachiness.ex.fm']
})


@roles('app')
def deploy():
    with cd('apps/mustachiness'):
        run('git pull')
        run('supervisorctl restart mustachiness')
