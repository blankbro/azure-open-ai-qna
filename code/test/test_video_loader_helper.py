def bilibili_test():
    from langchain.document_loaders import BiliBiliLoader

    loader = BiliBiliLoader(
        ["https://www.bilibili.com/video/BV1xt411o7Xu/"]
    )

    documents = loader.load()
    print(documents)


def youtube_test():
    from langchain.document_loaders import YoutubeLoader

    loader = YoutubeLoader.from_youtube_url("https://www.youtube.com/watch?v=QsYGlZkevEg", add_video_info=True)
    documents = loader.load()
    print(documents)


if __name__ == "__main__":
    # bilibili_test()
    youtube_test()
