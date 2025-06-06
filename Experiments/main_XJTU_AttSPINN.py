from dataloader.dataloader import XJTUdata
from Model.AttSPINN import count_parameters
from Model.AttSPINN import AttSPINN as SPINN
import argparse
import os
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

def calc_rmse(path):
    red_label = np.load(path+"/pred_label.npy")
    true_label = np.load(path+"/true_label.npy")
    rmse = np.sqrt(mean_squared_error(true_label, red_label))
    return rmse

def load_data(args,small_sample=None):
    root = 'data/XJTU data'
    data = XJTUdata(root=root, args=args)
    train_list = []
    test_list = []
    files = os.listdir(root)
    for file in files:
        if args.batch in file:
            if '4' in file or '8' in file:
                test_list.append(os.path.join(root, file))
            else:
                train_list.append(os.path.join(root, file))
    if small_sample is not None:
        train_list = train_list[:small_sample]

    train_loader = data.read_all(specific_path_list=train_list)
    test_loader = data.read_all(specific_path_list=test_list)
    dataloader = {'train': train_loader['train_2'],
                  'valid': train_loader['valid_2'],
                  'test': test_loader['test_3']}
    return dataloader


def main():
    args = get_args()
    batchs = ['2C', '3C', 'R2.5', 'R3', 'RW', 'satellite']
    for i in range(6):
        print(f'doing batch {i+1}')
        batch = batchs[i]
        setattr(args, 'batch', batch)
        for e in range(10):
            save_folder = 'results of reviewer/SPINN/XJTU results/' + str(i) + '-' + str(i) + '/Experiment' + str(e + 1)
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)
            log_dir = 'logging.txt'
            setattr(args, "save_folder", save_folder)
            setattr(args, "log_dir", log_dir)

            print("loading data...")
            dataloader = load_data(args)

            architecture_args = {
                "solution_u_subnet_args": {
                    "output_dim": 16,
                    "layers_num": 5,
                    "hidden_dim": 15,
                    "dropout": 0,
                    "activation": "leaky-relu"
                },
                "dynamical_F_subnet_args": {
                    "output_dim": 16,
                    "layers_num": 5,
                    "hidden_dim": 15,
                    "dropout": 0,
                    "activation": "leaky-relu"
                },
                "spinn_enabled": {"solution_u": True, "dynamical_F": True},

                # If you want to override attention dimension,
                # you can just put them here at top-level:
                "attn_embed_dim_u": 16,
                "attn_heads_u": 2,
                "attn_embed_dim_F": 16,
                "attn_heads_F": 2
            }

            spinn = SPINN(args, x_dim=17, architecture_args=architecture_args).cuda()
            print("---------------XXXXXXXX_________________")
            count_parameters(spinn)

            print("training...")
            spinn.Train(trainloader=dataloader['train'],validloader=dataloader['valid'],testloader=dataloader['test'])




def get_args():
    parser = argparse.ArgumentParser('Hyper Parameters for XJTU dataset')
    parser.add_argument('--data', type=str, default='XJTU', help='XJTU, HUST, MIT, TJU')
    parser.add_argument('--train_batch', type=int, default=0, choices=[-1,0,1,2,3,4,5],
                        help='(if -1, read all data and random split train and test sets; '
                             'else, read the corresponding batch data)')
    parser.add_argument('--test_batch', type=int, default=1, choices=[-1,0,1,2,3,4,5],
                        help='(if -1, read all data and random split train and test sets; '
                             'else, read the corresponding batch data)')
    parser.add_argument('--batch',type=str,default='2C',choices=['2C','3C','R2.5','R3','RW','satellite'])
    parser.add_argument('--batch_size', type=int, default=256, help='batch size')
    parser.add_argument('--normalization_method', type=str, default='min-max', help='min-max,z-score')

    # scheduler related
    parser.add_argument('--epochs', type=int, default=200, help='epoch')
    parser.add_argument('--early_stop', type=int, default=35, help='early stop')
    parser.add_argument('--warmup_epochs', type=int, default=30, help='warmup epoch')
    parser.add_argument('--warmup_lr', type=float, default=0.002, help='warmup lr')
    parser.add_argument('--lr', type=float, default=0.01, help='base lr')
    parser.add_argument('--final_lr', type=float, default=0.0002, help='final lr')
    parser.add_argument('--lr_F', type=float, default=0.001, help='lr of F')

    # model related
    parser.add_argument('--F_layers_num', type=int, default=3, help='the layers num of F')
    parser.add_argument('--F_hidden_dim', type=int, default=60, help='the hidden dim of F')

    # loss related
    parser.add_argument('--alpha', type=float, default=0.08549401305482651, help='loss = l_data + alpha * l_PDE + beta * l_physics')
    parser.add_argument('--beta', type=float, default=6.040426381151848, help='loss = l_data + alpha * l_PDE + beta * l_physics')

    parser.add_argument('--log_dir', type=str, default='text log.txt', help='log dir, if None, do not save')
    parser.add_argument('--save_folder', type=str, default='results of reviewer/SPINN/XJTU results', help='save folder')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()

