from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="cltl.speechsynthesis",
    description="The Leolani Speech Synthesis module for text to speech",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/leolani/cltl-speechsynthesis",
    license='MIT License',
    authors={
        "Baez Santamaria": ("Selene Baez Santamaria", "s.baezsantamaria@vu.nl"),
        "Baier": ("Thomas Baier", "t.baier@vu.nl")
    },
    package_dir={'': 'src'},
    packages=find_namespace_packages(include=['cltl.*']),
    python_requires='>=3.7.10',
    install_requires=['cltl.combot',
                      'requests==2.25.1',
                      'google-cloud-texttospeech==2.2.0',
                      'PyAudio==0.2.11',
                      'apispec==4.5.0',
                      'marshmallow-dataclass==8.4.1'
                      ],
    setup_requires=['flake8']
)