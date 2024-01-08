import os

c.GovernedRunner.log_level = 'DEBUG'
c.GovernedRunner.spawner_class = 'governedrunner.job.spawners.Repo2DockerSpawner'
c.GovernedRunner.builder_class = 'governedrunner.job.builders.DockerImageBuilder'

c.DockerSpawner.allowed_images = '*'
#c.DockerSpawner.remove = True
c.DockerImageBuilder.repo2docker_image = 'yacchin1205/repo2docker:feature_crate'
c.Repo2DockerSpawner.rdmfs_base_path = os.path.join(os.getcwd(), '.repo2docker/volumes')
