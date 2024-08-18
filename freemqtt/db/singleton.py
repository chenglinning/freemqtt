# -*- coding: utf-8 -*-
# Copyright (C) 2020-2028 
# Chenglin Ning, chenglinning@gmain.com
#

def singleton(cls, *args, **kw):
    instances = {}
    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton
