from dlgo.data.parallel_processor import GoDataProcessor
from dlgo.data.index_processor import KGSIndex

if __name__=='__main__':
    processor = GoDataProcessor(data_directory='C:/Users/User/PycharmProjects/dlgo/data/KGS')

    generator = processor.load_go_data('train', 100, use_generator=True)

    print(generator.get_num_samples())
    generator = generator.generate(batch_size=10)
    X, Y = generator.next()