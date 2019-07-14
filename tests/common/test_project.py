from pseudomat.common import project


def test_project_id():
    pid = project.project_id('johndoe@example.com', 'John’s first project')
    assert pid == 'RqEvrmGa0rbVo8JY6toXlR0m_nnBmh9w'
