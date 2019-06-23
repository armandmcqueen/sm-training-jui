from invoke import task





@task
def drun(c, name="sm_training_example:latest", vols="docker_logs:/logs", nvidia_docker=False, cmd="/bin/bash", cmd_args=""):
    """
    vols is a comma-separated list of HOST_DIR:CONTAINER_DIR pairs, e.g. ~/data:/data,~/logs:/logs
    """
    vol_pairs = vols.split(",")
    vol_args = ""
    for vol_pair in vol_pairs:
        vol_args += f' -v {vol_pair}'

    docker_bin = 'nvidia-docker' if nvidia_docker else 'docker'
    full_cmd = f'{docker_bin} run -it {vol_args} --entrypoint {cmd} {name} {cmd_args}'
    print(full_cmd)
    c.run(full_cmd, pty=True)

@task
def dbuild(c, name="sm_training_example:latest"):
    # c.run(f'docker build -t {name}:latest ../.. --build-arg CACHEBUST=$(date +%s) \
    # --build-arg BRANCH_NAME=${BRANCH_NAME}')
    c.run(f'docker build -t {name} .')
