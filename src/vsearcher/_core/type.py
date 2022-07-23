class _Type(list):
    """ 该类只作为变量类型的申明, 不能创建实例使用 """
    def __getitem__(self, key):
        return '1'
Type = _Type()